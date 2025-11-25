from flask import Flask, render_template, request, redirect, url_for, flash
from database import db
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
import os

import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

app = Flask(__name__)
app.logger.addHandler(handler)
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

scheduler.add_job(func=run_schedule, trigger="interval", minutes=60, id='access_check_job') # Run every hour
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
        
        # Save or update settings
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
        
        db.session.commit()
        flash('Settings updated successfully', 'success')
        
    plex_url = Settings.query.filter_by(key='plex_url').first()
    plex_token = Settings.query.filter_by(key='plex_token').first()
    
    return render_template('settings.html', 
                         plex_url=plex_url.value if plex_url else '',
                         plex_token=plex_token.value if plex_token else '')

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
