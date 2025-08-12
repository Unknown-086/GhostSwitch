GhostSwitch-Electron/
├── main.js                 # Main Electron process
├── preload.js             # Secure bridge
├── package.json
├── src/
│   ├── renderer/          # React frontend
│   │   ├── components/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── VPNDashboard.jsx
│   │   │   └── StatusIndicator.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   └── vpn.js
│   │   └── App.jsx
│   ├── main/              # Node.js backend
│   │   ├── services/
│   │   │   ├── wireguard.js
│   │   │   ├── vpn-manager.js
│   │   │   └── installer.js
│   │   └── config.js
│   └── shared/
│       └── constants.js
└── build/


# Initialize Electron project
npm init -y
npm install electron react react-dom
npm install --save-dev @electron/packager

# Additional dependencies
npm install node-fetch ws
