# 🗄️ PocketBase Manager

A web-based dashboard to create, manage, and monitor multiple PocketBase instances using PM2 process manager.

## ✨ Features

- 📦 **Create Instances** - Download and set up PocketBase instances with a few clicks
- 🎯 **Version Selection** - Choose from available PocketBase versions from GitHub releases
- ⚡ **Process Management** - Start, stop, restart instances via PM2
- 📊 **Status Monitoring** - Real-time status updates every 5 seconds
- 📝 **Log Viewer** - View PM2 logs directly from the dashboard
- 🔐 **Authentication** - Secure login system
- 🎨 **Modern UI** - Clean, responsive interface with TailwindCSS

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js** (for PM2)
- **PM2** - Install globally: `npm install -g pm2`

## 🚀 Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd PBManager
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

5. **Edit `.env` and configure your settings:**
   ```bash
   nano .env
   ```
   
   **Important:** Change the default admin credentials!

## ⚙️ Configuration

Edit the `.env` file to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key (change in production!) | - |
| `ADMIN_USERNAME` | Admin username | `admin` |
| `ADMIN_PASSWORD` | Admin password | `admin123` |
| `INSTANCES_DIR` | Directory to store PocketBase instances | `~/pocketbase-instances` |
| `DEFAULT_PORT_START` | Starting port for instances | `7200` |

## 🏃 Running

Start the application:

```bash
python app.py
```

Access the dashboard at: **http://127.0.0.1:5000**

Default credentials:
- **Username:** `admin`
- **Password:** `admin123`

## 📖 Usage

### Creating a New Instance

1. Click **"New Instance"** button
2. Enter instance name (e.g., `my-blog`)
3. Select PocketBase version
4. Optionally specify a port (auto-assigned if left empty)
5. Click **"Create"**

The manager will:
- Download the selected PocketBase version (if not cached)
- Create instance directory with proper structure:
  ```
  ~/pocketbase-instances/my-blog/
  ├── pocketbase (executable)
  ├── pb_hooks/
  ├── pb_migrations/
  └── pb_data/ (created on first run)
  ```
- Register the instance in the database

### Managing Instances

Each instance card provides buttons to:

- **▶️ Start** - Start the PocketBase instance with PM2
- **⏸️ Stop** - Stop the running instance
- **🔄 Restart** - Restart the instance
- **📝 Logs** - View PM2 logs (last 200 lines)
- **🗑️ Delete** - Remove instance (with confirmation)

### Accessing PocketBase Admin

Once an instance is running, click on its port number to open PocketBase admin UI in a new tab:

```
http://localhost:7200/_/
```

## 📁 Project Structure

```
PBManager/
├── app.py                    # Flask application entry point
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
│
├── core/                     # Business logic
│   ├── github_service.py     # GitHub API integration
│   ├── download_service.py   # PocketBase download management
│   ├── instance_service.py   # Instance CRUD operations
│   ├── pm2_service.py        # PM2 process control
│   └── auth_service.py       # Authentication
│
├── models/                   # Database models
│   ├── database.py           # SQLAlchemy setup
│   └── instance.py           # Instance model
│
├── routes/                   # Flask routes
│   ├── auth.py               # Login/logout
│   ├── dashboard.py          # Main dashboard
│   └── api.py                # REST API endpoints
│
├── templates/                # Jinja2 templates
│   ├── base.html
│   ├── login.html
│   └── dashboard.html
│
└── static/                   # Static assets
    ├── css/
    │   └── style.css
    └── js/
        ├── utils.js
        └── dashboard.js
```

## 🔧 API Endpoints

All API endpoints require authentication:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/versions` | Get available PocketBase versions |
| GET | `/api/instances` | List all instances with status |
| POST | `/api/instances` | Create new instance |
| GET | `/api/instances/<id>` | Get instance details |
| DELETE | `/api/instances/<id>` | Delete instance |
| POST | `/api/instances/<id>/start` | Start instance |
| POST | `/api/instances/<id>/stop` | Stop instance |
| POST | `/api/instances/<id>/restart` | Restart instance |
| GET | `/api/instances/<id>/logs` | Get instance logs |
| GET | `/api/instances/<id>/status` | Get instance status |

## 🛠️ Development

### Running in Debug Mode

Set in `.env`:
```
FLASK_DEBUG=True
```

### Database Location

SQLite database is stored at: `storage/instances.db`

### Instance Storage

All PocketBase instances are stored in the directory specified in `INSTANCES_DIR` (default: `~/pocketbase-instances/`)

Downloaded PocketBase versions are cached in: `~/pocketbase-instances/.downloads/`

## 🐛 Troubleshooting

### PM2 Commands Not Working

Ensure PM2 is installed globally:
```bash
npm install -g pm2
pm2 --version
```

### Port Already in Use

If the default port 7200 is in use, the manager will auto-increment to the next available port. You can also manually specify a port when creating an instance.

### Instance Won't Start

Check PM2 logs:
```bash
pm2 logs pb_<instance-name>
```

Or view logs through the dashboard's Logs button.

### Reset Admin Password

Delete the database and restart:
```bash
rm storage/instances.db
python app.py
```

## 📝 Notes

- **Auto-refresh**: Instance statuses refresh every 5 seconds
- **Port range**: Default port starts at 7200 and increments for each new instance
- **OS Support**: Automatically detects OS (Linux, macOS, Windows) and downloads appropriate PocketBase binary
- **Version cache**: Downloaded PocketBase versions are cached to speed up future instance creation

## 🔒 Security

- Change default admin credentials immediately
- Use a strong `SECRET_KEY` in production
- Consider setting up HTTPS for production deployments
- The dashboard is designed for local/trusted network use

## 📜 License

This project is open source and available for personal and commercial use.

## 🙏 Credits

- [PocketBase](https://pocketbase.io/) - Open source backend
- [PM2](https://pm2.keymetrics.io/) - Process manager
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [TailwindCSS](https://tailwindcss.com/) - CSS framework
