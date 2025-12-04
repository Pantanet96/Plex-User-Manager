# Plex User Manager

⚠️ **ALPHA VERSION** - This software is in early development.

**Plex User Manager** is a powerful web application designed to give you granular control over your Plex users' access. It allows you to schedule when users can access specific libraries, automatically granting or revoking permissions based on your rules.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## 🚀 Key Features

### 🛡️ Advanced Access Control
- **Granular Library Sharing**: Select exactly which libraries each user can access.
- **Scheduled Access**: Set **Start Dates** and **Expiration Dates** for temporary access.
- **Auto-Revocation**: Access is automatically removed when the expiration date is reached.
- **Default Library Protection**: Ensures users are never accidentally removed from the server by keeping a default library assigned.

### 🤖 Automation & Sync
- **Automatic Plex Sync**: Seamlessly imports users and libraries from your Plex server.
- **Background Scheduler**: Runs periodically (configurable from 5 minutes to daily) to enforce access rules.
- **Real-time Updates**: Changes made in the app are immediately pushed to Plex.

### ⚙️ Management & Monitoring
- **Role-Based Access**:
  - **Admin**: Full system control.
  - **Moderator**: Manage user access and libraries.
  - **Auditor**: Read-only view of logs and status.
- **Live Logs**: View, filter, and download application logs directly from the UI.
- **Server Control**: Restart the application and configure network settings (Port, HTTPS) from the dashboard.

### 🎨 Modern Experience
- **Beautiful UI**: Dark mode interface with glassmorphism design.
- **Secure**: Local authentication with password complexity enforcement.

---

## 📸 Screenshots

### Dashboard
Overview of all users and their current status.
![Dashboard](https://raw.githubusercontent.com/Pantanet96/Plex-User-Manager/main/docs/screenshots/dashboard.png)

### Access Management
Easily configure which libraries a user can access and for how long.
![Manage Access](https://raw.githubusercontent.com/Pantanet96/Plex-User-Manager/main/docs/screenshots/manage-access.png)

---

## 🛠️ Installation & Setup

### 🐳 Docker (Recommended)

The easiest way to run Plex User Manager is with Docker.

1. **Run the container**:
   ```bash
   docker run -d \
     -p 5000:5000 \
     -v ./data:/app/instance \
     -e SECRET_KEY=change-me-in-production \
     --name plex-manager \
     pantanet96/plex-user-manager:latest
   ```

2. **Access the UI**: Open `http://localhost:5000`
3. **Default Credentials**: `admin` / `admin` (Change immediately!)

👉 **[View Detailed Docker Guide](DOCKER.md)** for Compose setups, environment variables, and troubleshooting.

### 🐍 Manual Installation (Python)

1. Clone the repo and install dependencies:
   ```bash
   git clone https://github.com/Pantanet96/Plex-User-Manager.git
   cd Plex-User-Manager
   pip install -r requirements.txt
   ```
2. Initialize the database:
   ```bash
   python init_db.py
   ```
3. Run the app:
   ```bash
   python app.py
   ```

---

## 📖 User Guide

### 1. Initial Configuration
1. Log in with `admin` / `admin`.
2. Go to **Settings**.
3. Enter your **Plex Server URL** (e.g., `http://192.168.1.100:32400`) and **Plex Token**.
4. Save Settings.

### 2. Syncing Users
1. Go to the **Dashboard**.
2. Click **Sync with Plex**. This will pull all your current Plex users and libraries into the local database.

### 3. Managing Access
1. On the Dashboard, click **Manage Access** for a user.
2. Check the libraries you want them to access.
3. (Optional) Set a **Start Date** if you want access to begin in the future.
4. (Optional) Set an **Expiration Date** if you want access to end automatically.
5. Click **Save Changes**.

### 4. Scheduler Settings
By default, the scheduler runs every hour. You can change this in **Settings** > **Scheduler Configuration**:
- **Interval Mode**: Run every X minutes.
- **Daily Mode**: Run once a day at a specific time.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 📄 License

This project is licensed under the MIT License.
