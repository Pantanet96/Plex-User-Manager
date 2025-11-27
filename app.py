from flask import Flask, render_template, request, redirect, url_for, flash
from database import db
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
import os
import sys


import logging
from logging.handlers import RotatingFileHandler

# Configure logging with rotation
# Remove any existing handlers
logging.getLogger().handlers = []

# Create formatters
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_formatter = logging.Formatter('%(levelname)s: %(message)s')

# App log handler (INFO and above) - 10MB max, 5 backups
app_handler = RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5)
app_handler.setLevel(logging.INFO)
app_handler.setFormatter(file_formatter)

# Error log handler (ERROR only) - 10MB max, 5 backups
error_handler = RotatingFileHandler('error.log', maxBytes=10*1024*1024, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(file_formatter)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

# Configure root logger
logging.basicConfig(level=logging.INFO, handlers=[app_handler, error_handler, console_handler])

app = Flask(__name__)
app.logger.addHandler(app_handler)
app.logger.addHandler(error_handler)
app.logger.setLevel(logging.INFO)

app.config['SECRET_KEY'] = 'your_secret_key_here' # TODO: Change this to a secure random key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plex_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Role-based access control decorators
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            app.logger.warning(f'Unauthorized access attempt by {current_user.username} to admin route: {f.__name__}')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def moderator_required(f):
    """Decorator for moderator+ routes (moderator and admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_moderator():
            flash('Access denied. Moderator privileges required.', 'error')
            app.logger.warning(f'Unauthorized access attempt by {current_user.username} to moderator route: {f.__name__}')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def auditor_required(f):
    """Decorator for all authenticated users (auditor+)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        # All authenticated users can access auditor routes
        return f(*args, **kwargs)
    return decorated_function

@app.route('/restart', methods=['POST'])
@login_required
@admin_required
def restart_server():
    """Restarts the application by exiting with code 1."""
    try:
        app.logger.info('Restart requested by user. Exiting with code 1...')
        flash('Server is restarting...', 'info')
        
        # Exit with code 1 to signal that a restart is needed
        # In Docker, this will trigger the container to restart (with restart policy)
        # On bare metal, you'll need to use a process manager like systemd or supervisor
        def shutdown():
            os._exit(1)
        
        # Schedule shutdown after response is sent
        from threading import Timer
        Timer(0.5, shutdown).start()
        
        return redirect(url_for('settings'))
    except Exception as e:
        flash(f'Error restarting server: {str(e)}', 'error')
        return redirect(url_for('settings'))

scheduler = BackgroundScheduler()

def run_schedule():
    with app.app_context():
        from plex_service import check_schedules
        check_schedules()

def get_scheduler_settings():
    """Get scheduler settings from database with defaults"""
    with app.app_context():
        from models import Settings
        
        scheduler_type = Settings.query.filter_by(key='scheduler_type').first()
        interval_minutes = Settings.query.filter_by(key='scheduler_interval_minutes').first()
        daily_time = Settings.query.filter_by(key='scheduler_daily_time').first()
        
        return {
            'type': scheduler_type.value if scheduler_type else 'interval',
            'interval_minutes': int(interval_minutes.value) if interval_minutes else 60,
            'daily_time': daily_time.value if daily_time else '03:00'
        }

def configure_scheduler():
    """Configure scheduler based on database settings"""
    settings = get_scheduler_settings()
    
    # Remove existing job if it exists
    if scheduler.get_job('access_check_job'):
        scheduler.remove_job('access_check_job')
    
    # Add job based on type
    if settings['type'] == 'daily':
        # Parse time string (HH:MM)
        hour, minute = map(int, settings['daily_time'].split(':'))
        scheduler.add_job(
            func=run_schedule,
            trigger='cron',
            hour=hour,
            minute=minute,
            id='access_check_job'
        )
        app.logger.info(f"Scheduler configured for daily execution at {settings['daily_time']}")
    else:
        # Interval mode
        scheduler.add_job(
            func=run_schedule,
            trigger='interval',
            minutes=settings['interval_minutes'],
            id='access_check_job'
        )
        app.logger.info(f"Scheduler configured for interval execution every {settings['interval_minutes']} minutes")

# Initialize scheduler with settings
configure_scheduler()
scheduler.start()

from models import User, Settings, PlexUser, Library, Share

def get_setting(key, default=None):
    """Get a setting value from the database"""
    setting = Settings.query.filter_by(key=key).first()
    if setting:
        return setting.value
    return default

def update_setting(key, value):
    """Update or create a setting in the database"""
    setting = Settings.query.filter_by(key=key).first()
    if not setting:
        setting = Settings(key=key)
        db.session.add(setting)
    setting.value = value
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    users = PlexUser.query.all()
    libraries = Library.query.all()
    
    job = scheduler.get_job('access_check_job')
    next_run = job.next_run_time if job else None
    
    return render_template('dashboard.html', users=users, libraries=libraries, next_run=next_run)

def update_server_settings():
    try:
        server_port = request.form.get('server_port')
        https_enabled = 'https_enabled' in request.form
        ssl_type = request.form.get('ssl_type')
        
        update_setting('server_port', server_port)
        update_setting('https_enabled', 'true' if https_enabled else 'false')
        update_setting('ssl_type', ssl_type)
        
        if https_enabled:
            cert_dir = os.path.join(app.root_path, 'certs')
            os.makedirs(cert_dir, exist_ok=True)
            
            if ssl_type == 'custom':
                cert_file = request.files.get('ssl_cert')
                key_file = request.files.get('ssl_key')
                
                if cert_file and cert_file.filename:
                    cert_path = os.path.join(cert_dir, 'custom.crt')
                    cert_file.save(cert_path)
                    update_setting('ssl_cert_path', cert_path)
                    
                if key_file and key_file.filename:
                    key_path = os.path.join(cert_dir, 'custom.key')
                    key_file.save(key_path)
                    update_setting('ssl_key_path', key_path)
            else:
                # Generate self-signed if needed
                cert_path = os.path.join(cert_dir, 'selfsigned.crt')
                key_path = os.path.join(cert_dir, 'selfsigned.key')
                
                if not os.path.exists(cert_path) or not os.path.exists(key_path):
                    from ssl_utils import generate_self_signed_cert
                    generate_self_signed_cert(cert_path, key_path)
                
                update_setting('ssl_cert_path', cert_path)
                update_setting('ssl_key_path', key_path)
        
        flash('Server settings updated. Please restart the application to apply changes.', 'success')
    except Exception as e:
        flash(f'Error updating server settings: {str(e)}', 'error')
        
    return redirect(url_for('settings'))

def update_scheduler_settings():
    scheduler_type = request.form.get('scheduler_type')
    interval = request.form.get('scheduler_interval_minutes')
    daily_time = request.form.get('scheduler_daily_time')
    
    update_setting('scheduler_type', scheduler_type)
    update_setting('scheduler_interval_minutes', interval)
    update_setting('scheduler_daily_time', daily_time)
    
    configure_scheduler()
    flash('Scheduler settings updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not current_user.can_edit_settings():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Handle Password Change
        if 'current_password' in request.form:
            return change_password()
            
        # Handle Scheduler Config
        if 'scheduler_type' in request.form:
            return update_scheduler_settings()
            
        # Handle Server Config
        if 'server_port' in request.form:
            return update_server_settings()
            
        # Handle Plex Settings
        plex_url = request.form.get('plex_url')
        plex_token = request.form.get('plex_token')
        
        if plex_url and plex_token:
            update_setting('plex_url', plex_url)
            update_setting('plex_token', plex_token)
            flash('Plex settings updated successfully', 'success')
        
        return redirect(url_for('settings'))
    
    # Get all settings
    plex_url = get_setting('plex_url')
    plex_token = get_setting('plex_token')
    
    # Scheduler settings
    scheduler_settings = get_scheduler_settings()
    
    # Server settings
    server_port = get_setting('server_port', '5000')
    https_enabled = get_setting('https_enabled', 'false') == 'true'
    ssl_type = get_setting('ssl_type', 'self-signed')
    
    return render_template('settings.html', 
                         plex_url=plex_url, 
                         plex_token=plex_token,
                         scheduler_type=scheduler_settings['type'],
                         scheduler_interval_minutes=scheduler_settings['interval_minutes'],
                         scheduler_daily_time=scheduler_settings['daily_time'],
                         server_port=server_port,
                         https_enabled=https_enabled,
                         ssl_type=ssl_type)

def validate_password(password):
    """
    Validate password meets security requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one number
    - At least one special character
    Returns (is_valid, error_message)
    """
    import re
    
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    
    # Check for at least one number
    if not re.search(r'[0-9]', password):
        return False, 'Password must contain at least one number'
    
    # Check for at least one special character
    special_chars = r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]'
    if not re.search(special_chars, password):
        return False, 'Password must contain at least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\\/;~`)'
    
    return True, ''

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Incorrect current password', 'error')
        return redirect(url_for('settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('settings'))
    
    # Validate password strength
    is_valid, error_message = validate_password(new_password)
    if not is_valid:
        flash(error_message, 'error')
        return redirect(url_for('settings'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/run_scheduler', methods=['POST'])
@admin_required
def run_scheduler():
    """Manual trigger for scheduler - for debugging purposes"""
    from plex_service import check_schedules
    try:
        check_schedules()
        flash('Scheduler executed successfully', 'success')
    except Exception as e:
        flash(f'Scheduler failed: {str(e)}', 'error')
    return redirect(url_for('settings'))

@app.route('/sync_plex', methods=['POST'])
@moderator_required
def sync_plex():
    from plex_service import sync_plex_data
    success, message = sync_plex_data()
    if success:
        flash(message, 'success')
    else:
        flash(f'Error: {message}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@auditor_required
def user_details(user_id):
    user = PlexUser.query.get_or_404(user_id)
    libraries = Library.query.all()
    
    if request.method == 'POST':
        if not current_user.can_edit_libraries():
            flash('Access denied. Moderator privileges required to edit access.', 'error')
            return redirect(url_for('user_details', user_id=user.id))
            
        from plex_service import update_user_access
        from datetime import datetime
        
        active_library_keys = []
        
        for lib in libraries:
            is_checked = request.form.get(f'library_{lib.id}') == 'on'
            start_date_str = request.form.get(f'start_date_{lib.id}')
            expiration_date_str = request.form.get(f'expiration_date_{lib.id}')
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
            expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d') if expiration_date_str else None
            
            # Update Share model
            share = Share.query.filter_by(plex_user_id=user.id, library_id=lib.id).first()
            if not share:
                share = Share(plex_user_id=user.id, library_id=lib.id)
                db.session.add(share)
            
            share.is_active = is_checked
            share.start_date = start_date
            share.expiration_date = expiration_date
            
            # Determine if we should share this library with Plex NOW
            # Logic: If is_active AND (start_date is None OR start_date <= now) AND (expiration_date is None OR expiration_date > now)
            now = datetime.now()
            should_share = is_checked
            if start_date and start_date > now:
                should_share = False
            if expiration_date and expiration_date <= now:
                should_share = False
                
            if should_share:
                active_library_keys.append(lib.plex_key)
        
        db.session.commit()
        
        # Update Plex
        success, message = update_user_access(user.plex_id, active_library_keys)
        if success:
            flash('Access updated successfully on Plex.', 'success')
        else:
            flash(f'Local saved, but Plex update failed: {message}', 'error')
            
        return redirect(url_for('user_details', user_id=user.id))
        
    return render_template('user_details.html', user=user, libraries=libraries)


# Log Management Helper Functions
def parse_log_file(filename, max_lines=100, level_filter=None):
    """Parse log file and return recent entries with optional level filtering"""
    import os
    from collections import deque
    
    if not os.path.exists(filename):
        return []
    
    log_entries = deque(maxlen=max_lines)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Apply level filter if specified
                if level_filter:
                    if f' - {level_filter} - ' not in line:
                        continue
                
                # Parse log line
                try:
                    parts = line.split(' - ', 3)
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        logger_name = parts[1]
                        level = parts[2]
                        message = parts[3]
                        
                        log_entries.append({
                            'timestamp': timestamp,
                            'logger': logger_name,
                            'level': level,
                            'message': message
                        })
                    else:
                        # Fallback for malformed lines
                        log_entries.append({
                            'timestamp': '',
                            'logger': '',
                            'level': 'UNKNOWN',
                            'message': line
                        })
                except Exception:
                    # If parsing fails, add as raw message
                    log_entries.append({
                        'timestamp': '',
                        'logger': '',
                        'level': 'UNKNOWN',
                        'message': line
                    })
        
        return list(log_entries)
    except Exception as e:
        app.logger.error(f'Error reading log file {filename}: {str(e)}')
        return []


@app.route('/api/logs', methods=['GET'])
@auditor_required
def get_logs():
    """API endpoint to get recent log entries"""
    from flask import jsonify
    
    # Get query parameters
    log_file = request.args.get('file', 'app')  # 'app' or 'error'
    level = request.args.get('level', None)  # Filter by level
    lines = request.args.get('lines', 100, type=int)  # Number of lines
    
    # Validate parameters
    if log_file not in ['app', 'error']:
        return jsonify({'error': 'Invalid log file. Use "app" or "error"'}), 400
    
    if lines < 1 or lines > 1000:
        return jsonify({'error': 'Lines must be between 1 and 1000'}), 400
    
    if level and level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        return jsonify({'error': 'Invalid log level'}), 400
    
    # Get log filename
    filename = f'{log_file}.log'
    
    # Parse and return logs
    logs = parse_log_file(filename, max_lines=lines, level_filter=level)
    
    return jsonify({
        'file': log_file,
        'level_filter': level,
        'count': len(logs),
        'logs': logs
    })


@app.route('/api/logs/download', methods=['GET'])
@admin_required
def download_logs():
    """API endpoint to download complete log file"""
    from flask import send_file
    import os
    
    log_file = request.args.get('file', 'app')
    
    if log_file not in ['app', 'error']:
        flash('Invalid log file', 'error')
        return redirect(url_for('settings'))
    
    filename = f'{log_file}.log'
    
    if not os.path.exists(filename):
        flash(f'Log file {filename} not found', 'error')
        return redirect(url_for('settings'))
    
    return send_file(filename, as_attachment=True, download_name=filename)




@app.route('/users')
@admin_required
def users():
    """User management page"""
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

@app.route('/users/create', methods=['POST'])
@admin_required
def create_user():
    """Create a new user"""
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('users'))
    
    # Validate password
    is_valid, error_message = validate_password(password)
    if not is_valid:
        flash(error_message, 'error')
        return redirect(url_for('users'))
    
    # Validate role
    if role not in User.ROLES:
        flash('Invalid role', 'error')
        return redirect(url_for('users'))
    
    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash(f'User {username} created successfully', 'success')
    return redirect(url_for('users'))

@app.route('/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def edit_user(user_id):
    """Edit user role or password"""
    user = User.query.get_or_404(user_id)
    
    # Prevent editing self role (to avoid locking self out)
    if user.id == current_user.id:
        flash('You cannot edit your own role from here. Use Settings to change password.', 'warning')
        return redirect(url_for('users'))
        
    role = request.form.get('role')
    password = request.form.get('password')
    
    if role and role in User.ROLES:
        user.role = role
        
    if password:
        # Validate password
        is_valid, error_message = validate_password(password)
        if not is_valid:
            flash(error_message, 'error')
            return redirect(url_for('users'))
        user.set_password(password)
        
    db.session.commit()
    flash(f'User {user.username} updated successfully', 'success')
    return redirect(url_for('users'))

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('You cannot delete yourself', 'error')
        return redirect(url_for('users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} deleted successfully', 'success')
    return redirect(url_for('users'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Get server config
        port = int(get_setting('server_port', '5000'))
        https_enabled = get_setting('https_enabled', 'false') == 'true'
        
        ssl_context = None
        if https_enabled:
            cert_path = get_setting('ssl_cert_path')
            key_path = get_setting('ssl_key_path')
            
            if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
                ssl_context = (cert_path, key_path)
            else:
                print("Warning: HTTPS enabled but certificates not found. Falling back to HTTP.")
    
    app.run(host='0.0.0.0', port=port, ssl_context=ssl_context, debug=True)
