# GhostSwitch# GhostSwitch VPN

![GhostSwitch Logo](https://img.shields.io/badge/GhostSwitch-VPN-brightgreen)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

A self-hosted, privacy-focused VPN solution with minimal cost and maximum control.

## 📑 Contents

- Overview
- Features
- Architecture
- Prerequisites
- Server Setup
- Client Installation
- Usage Guide
- Security Considerations
- Project Structure
- Future Work
- Troubleshooting

## 🔍 Overview

GhostSwitch is a self-hosted VPN platform that lets individuals and small teams deploy their own privacy-preserving VPN at minimal cost (e.g., AWS free tier or low-cost VPS). The system automates server provisioning, peer management, and client setup using a Flask API backend, a Windows Electron client, and WireGuard for fast, modern tunneling.

Unlike commercial VPN services, GhostSwitch gives you complete control over your data, servers, and connection logs, all while maintaining high performance and security.

## ✨ Features

- **Self-hosted VPN** using WireGuard protocol (UDP, high performance)
- **User-friendly Windows client** with one-click connect/disconnect
- **Multi-user support** with user registration and authentication
- **Server management** - ability to add multiple server locations
- **Connection logging** and data usage tracking
- **Automatic IP assignment** for new clients
- **Fast connection speeds** with minimal overhead
- **Secure** with modern cryptography (WireGuard)
- **Duration timer** to track connection time
- **Connection verification** with multiple methods

## 🏗️ Architecture

GhostSwitch consists of three main components:

### Backend (Flask API + MySQL)
- Provides authentication, server discovery, VPN configuration generation, and connection logging
- Stores users, servers, assigned IPs, WireGuard keys, and connection logs
- On "generate config," allocates an IP, creates client keys, updates the server's wg0.conf, and returns a ready-to-use .conf

### VPN Layer (WireGuard)
- Each server runs WireGuard (wg0)
- Peers (clients) are added dynamically via the API
- Configuration updates follow a safe sequence to ensure consistency

### Client (Electron App for Windows)
- Provides a GUI to log in, pick a server, and connect
- Uses the official WireGuard CLI to import the config and start a tunnel
- Handles disconnect and reconnect scenarios
- Shows connection status and duration

## 📋 Prerequisites

### Server
- Ubuntu server (20.04 LTS or later recommended)
- Public IP address
- Port 51820/UDP open (WireGuard)
- Port 5000/TCP open (API)
- Root or sudo access

### Client
- Windows 10/11
- WireGuard for Windows installed
- Internet connection

## 🖥️ Server Setup

1. Provision an Ubuntu VM (AWS, DigitalOcean, or any VPS provider)

2. Install required packages:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv mysql-client wireguard
   ```

3. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ghostswitch.git
   cd ghostswitch/Server
   ```

4. Setup Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. Setup the database:
   ```bash
   bash DatabaseSetup.sh
   ```

6. Configure WireGuard:
   ```bash
   sudo bash WireGuardSetup.sh
   ```

7. Run as a service:
   ```bash
   sudo nano /etc/systemd/system/ghostswitch.service
   
   # Add the following content:
   [Unit]
   Description=GhostSwitch VPN API Server
   After=network.target mysql.service

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/ghostswitch/Server
   ExecStart=/home/ubuntu/ghostswitch/Server/venv/bin/python3 FlaskAPI.py
   Restart=always
   StandardOutput=append:/var/log/ghostswitch/api.log
   StandardError=append:/var/log/ghostswitch/error.log

   [Install]
   WantedBy=multi-user.target
   ```

8. Start the service:
   ```bash
   sudo mkdir -p /var/log/ghostswitch
   sudo chown ubuntu:ubuntu /var/log/ghostswitch
   sudo systemctl daemon-reload
   sudo systemctl enable ghostswitch
   sudo systemctl start ghostswitch
   ```

## 💻 Client Installation

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ghostswitch.git
   cd ghostswitch/Client/Electron
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Update API endpoint:
   Edit `src/renderer/services/real-api.js` and update the baseURL with your server IP:
   ```javascript
   this.baseURL = 'http://YOUR_SERVER_IP:5000/api';
   ```

4. Run the app:
   ```bash
   npm start
   ```

### User Installation

1. Install WireGuard for Windows from [wireguard.com](https://www.wireguard.com/install/)
2. Download the GhostSwitch installer
3. Run the installer and follow on-screen instructions
4. Launch GhostSwitch

## 🚀 Usage Guide

### First-Time Setup

1. **Register an account**: Open GhostSwitch and click "Sign Up" to create a new account
2. **Login**: Enter your credentials to log in
3. **Select a server**: Choose from available server locations

### Connect to VPN

1. Select your desired server location
2. Click "Connect VPN"
3. Wait for the connection to establish (status will change to "Connected")
4. Your connection is now secure and private

### Disconnect from VPN

1. Click "Disconnect VPN"
2. Wait for the disconnection process to complete
3. You'll return to your regular internet connection

## 🔒 Security Considerations

- **Transport security**: WireGuard's modern cryptography with optional preshared keys
- **Authentication**: JWT tokens (short-lived) and hashed passwords for user accounts
- **Key handling**: Server private keys stay on the server; client private keys are generated per device
- **Least privilege**: Sudoers entries narrowly scoped to required WireGuard operations
- **Config hygiene**: Always brings interface down before making changes, then up
- **Connection verification**: Multiple methods to verify VPN connection status

## 📁 Project Structure

```
GhostSwitch/
├── Client/
│   └── Electron/
│       ├── main.js            # Electron main process
│       ├── preload.js         # Preload script for IPC
│       ├── package.json       # Dependencies and scripts
│       └── src/
│           ├── main/          # Main process code
│           │   └── services/  # Main process services
│           ├── renderer/      # UI code
│           │   ├── components/# UI components
│           │   ├── services/  # API and VPN services
│           │   └── react-index.html # Main UI
│           └── shared/        # Shared code
└── Server/
    ├── FlaskAPI.py           # Main API server
    ├── DatabaseSetup.sh      # Database setup script
    └── WireGuardSetup.sh     # WireGuard setup script
```

## 🔮 Future Work

- **OpenVPN support**: Add TCP mode for users prioritizing reliability over speed
- **Mobile clients**: Android and iOS app versions
- **HTTPS**: Add Let's Encrypt for API security
- **Multi-region**: Auto-selection and health-based failover
- **Bandwidth limits**: Per-user rate and volume restrictions
- **Automated bootstrap**: One-command new server enrollment
- **Linux/macOS clients**: Support for additional platforms

## 🔧 Troubleshooting

### Server Issues

- **API not accessible**: Check firewall settings for port 5000/TCP
- **VPN connection fails**: Ensure port 51820/UDP is open
- **Database connection error**: Verify MySQL credentials and service status

### Client Issues

- **Cannot connect to server**: Verify server IP address in API configuration
- **WireGuard detection fails**: Ensure WireGuard is installed correctly
- **Connection fails**: Check for existing tunnel (may need to disconnect first)
- **Duration timer not updating**: Restart the application

For additional support, please open an issue in the GitHub repository.

---
