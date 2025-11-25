from flask import Flask, render_template, request, redirect, url_for, flash
from database import db
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
import os

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

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        plex_url = request.form.get('plex_url')
        plex_token = request.form.get('plex_token')
        scheduler_type = request.form.get('scheduler_type')
        scheduler_interval = request.form.get('scheduler_interval_minutes')
        scheduler_time = request.form.get('scheduler_daily_time')
        
        # Save or update Plex settings
        url_setting = Settings.query.filter_by(key='plex_url').first()
        if not url_setting:
            url_setting = Settings(key='plex_url')
            db.session.add(url_setting)
        url_setting.value = plex_url
        
        token_setting = Settings.query.filter_by(key='plex_token').first()
        if not token_setting:
            token_setting = Settings(key='plex_token')
            db.session.add(token_setting)
        token_setting.value = plex_token
        
        # Save scheduler settings
        type_setting = Settings.query.filter_by(key='scheduler_type').first()
        if not type_setting:
            type_setting = Settings(key='scheduler_type')
            db.session.add(type_setting)
        type_setting.value = scheduler_type
        
        interval_setting = Settings.query.filter_by(key='scheduler_interval_minutes').first()
        if not interval_setting:
            interval_setting = Settings(key='scheduler_interval_minutes')
            db.session.add(interval_setting)
        interval_setting.value = scheduler_interval
        
        time_setting = Settings.query.filter_by(key='scheduler_daily_time').first()
        if not time_setting:
            time_setting = Settings(key='scheduler_daily_time')
            db.session.add(time_setting)
        time_setting.value = scheduler_time
        
        db.session.commit()
        
        # Reconfigure scheduler with new settings
        configure_scheduler()
        
        flash('Settings updated successfully', 'success')
        
    # Get current settings
    plex_url = Settings.query.filter_by(key='plex_url').first()
    plex_token = Settings.query.filter_by(key='plex_token').first()
    
    # Get scheduler settings with defaults
    scheduler_settings = get_scheduler_settings()
    
    return render_template('settings.html', 
                         plex_url=plex_url.value if plex_url else '',
                         plex_token=plex_token.value if plex_token else '',
                         scheduler_type=scheduler_settings['type'],
                         scheduler_interval_minutes=scheduler_settings['interval_minutes'],
                         scheduler_daily_time=scheduler_settings['daily_time'])

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
        
    if len(new_password) < 4:
        flash('Password must be at least 4 characters long', 'error')
        return redirect(url_for('settings'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/run_scheduler', methods=['POST'])
@login_required
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
@login_required
def sync_plex():
    from plex_service import sync_plex_data
    success, message = sync_plex_data()
    if success:
        flash(message, 'success')
    else:
        flash(f'Error: {message}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_details(user_id):
    user = PlexUser.query.get_or_404(user_id)
    libraries = Library.query.all()
    
    if request.method == 'POST':
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
@login_required
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
@login_required
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



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
