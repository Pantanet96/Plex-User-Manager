# Plex User Library Management

A modern web application for managing Plex library sharing with scheduled access control and expiration dates.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- 🎯 **Manual Library Sharing**: Easily manage which libraries each user can access
- ⏰ **Scheduled Access**: Set start and expiration dates for library access
- 🔄 **Automatic Sync**: Import users and libraries from your Plex server
- 📅 **Configurable Scheduler**: Customize scheduler frequency (5 minutes to daily) or run at specific times
- 📝 **Log Management**: Real-time log viewing with filtering, auto-refresh, and download capabilities
- 🎨 **Modern UI**: Beautiful dark theme with glassmorphism effects
- 🔐 **Local Authentication**: Secure admin login with password change functionality
- 🔑 **Password Visibility Toggle**: Show/hide passwords with SVG eye icons
- 📊 **Real-time Updates**: Changes are immediately reflected on Plex
- 🛡️ **Default Library Protection**: Prevents user removal by maintaining a default library assignment

## Screenshots

*Coming soon*

## Prerequisites

- Python 3.8 or higher
- A Plex Media Server
- Plex Pass (required for sharing libraries)
- Plex Authentication Token ([How to find your token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/))

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Pantanet96/Plex-User-Manager.git
   cd Plex-User-Manager
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the database**
   ```bash
   python init_db.py
   ```
   This creates the SQLite database and a default admin user (`admin`/`admin`).

## Configuration

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Access the web interface**
   - Open your browser and navigate to `http://127.0.0.1:5000`
   - Login with default credentials: `admin` / `admin`

3. **Configure Plex settings**
   - Go to Settings
   - Enter your Plex Server URL (e.g., `http://192.168.1.100:32400`)
   - Enter your Plex Authentication Token
   - Click "Save Settings"

4. **Sync with Plex**
   - Go to Dashboard
   - Click "Sync with Plex" to import users and libraries

## Usage

### Managing User Access

1. Click on "Manage Access" for any user in the dashboard
2. Select which libraries the user should have access to
3. Optionally set start and expiration dates
4. Click "Save Changes"

**Note**: The "Default" library is always assigned and cannot be removed to prevent user removal from the server.

### Scheduled Access

- Set a **Start Date** to grant access beginning at a specific time
- Set an **Expiration Date** to automatically revoke access after a certain date
- Leave dates empty for immediate and permanent access
- The background scheduler automatically applies date-based changes

### Scheduler Configuration

You can customize how often the scheduler runs:

1. Go to **Settings**
2. Scroll to **Scheduler Configuration**
3. Choose between two modes:
   - **Interval Mode**: Run every X minutes (5-1440 minutes)
   - **Daily Mode**: Run once per day at a specific time (e.g., 03:00)
4. Click **Save Settings**

The scheduler will automatically reconfigure without requiring an app restart.

### Manual Scheduler Trigger


For testing purposes, you can manually trigger the scheduler:
1. Go to Settings
2. Scroll to "Debug Tools"
3. Click "Run Scheduler Now"

### Log Management

View and monitor application logs directly from the Settings page:

1. Go to **Settings**
2. Scroll to **Application Logs**
3. Select log file:
   - **Application Logs**: All application activity (INFO, WARNING, ERROR)
   - **Error Logs**: Only error messages
4. Filter by log level (DEBUG, INFO, WARNING, ERROR)
5. Adjust number of lines to display (10-1000)
6. Enable/disable auto-refresh (updates every 5 seconds)
7. Download complete log files for offline analysis

**Log Rotation**: Log files are automatically rotated when they reach 10MB, keeping the last 5 backup files (50MB total per log type).

## Security Considerations

⚠️ **Important**: Before deploying to production:

1. **Change the default admin password**
   - The default credentials (`admin`/`admin`) should be changed immediately

2. **Update the SECRET_KEY**
   - In `app.py`, replace `your_secret_key_here` with a secure random key:
     ```python
     import secrets
     print(secrets.token_hex(32))
     ```

3. **SSL/TLS Configuration**
   - The application currently disables SSL verification for Plex connections
   - For production, implement proper SSL certificate handling

4. **Use a production WSGI server**
   - Don't use Flask's development server in production
   - Consider using Gunicorn, uWSGI, or similar

## Project Structure

```
Plex-User-Manager/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── database.py            # Database initialization
├── plex_service.py        # Plex API integration
├── init_db.py             # Database setup script
├── requirements.txt       # Python dependencies
├── static/
│   └── style.css          # Application styling
└── templates/
    ├── base.html          # Base template
    ├── login.html         # Login page
    ├── dashboard.html     # Main dashboard
    ├── settings.html      # Settings page
    └── user_details.html  # User management page
```

## Technologies Used

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login
- **Database**: SQLite
- **Scheduler**: APScheduler
- **Plex Integration**: PlexAPI
- **Frontend**: HTML, CSS (Glassmorphism design), Vanilla JavaScript

## Troubleshooting

### Plex Connection Issues

If you encounter SSL certificate errors:
- The application is configured to bypass SSL verification for local Plex servers
- Check that your Plex Server URL and Token are correct in Settings

### Scheduler Not Running

- Check the countdown timer on the dashboard
- Manually trigger the scheduler from Settings > Debug Tools
- Check `app.log` for error messages

### Database Issues

If you need to reset the database:
```bash
rm plex_manager.db
python init_db.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [PlexAPI](https://github.com/pkkid/python-plexapi)
- Inspired by the need for better Plex library management

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Note**: This application is not affiliated with or endorsed by Plex Inc.
