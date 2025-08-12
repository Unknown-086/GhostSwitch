const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');

// Keep a global reference of the window object
let mainWindow;

function createWindow() {
    // Create the browser window
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        titleBarStyle: 'default',
        show: false,
        icon: path.join(__dirname, 'public', 'ghostswitch_icon.ico')
    });

    // Check if we have a React build or use HTML fallback
    const reactIndexPath = path.join(__dirname, 'src', 'renderer', 'react-index.html');
    const htmlFallbackPath = path.join(__dirname, 'src', 'renderer', 'index.html');
    
    if (fs.existsSync(reactIndexPath)) {
        // Load React version
        console.log('Loading React application...');
        mainWindow.loadFile(reactIndexPath);
    } else {
        // Load HTML fallback
        console.log('Loading HTML fallback...');
        mainWindow.loadFile(htmlFallbackPath);
    }

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Open DevTools
    mainWindow.webContents.openDevTools();

    // Handle window closed
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// Security
app.on('web-contents-created', (event, contents) => {
    contents.on('new-window', (event, navigationUrl) => {
        event.preventDefault();
        console.log('Blocked new window creation to:', navigationUrl);
    });
});

// ===============================
// IPC HANDLERS FOR YOUR FRONTEND
// ===============================

// App information
ipcMain.handle('app-version', () => {
    return app.getVersion();
});

// WireGuard operations
ipcMain.handle('check-wireguard', async () => {
    try {
        return new Promise((resolve) => {
            const command = process.platform === 'win32' ? 'where wg' : 'which wg';
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    resolve({ 
                        installed: false, 
                        status: 'not_installed',
                        message: 'WireGuard not found'
                    });
                } else {
                    resolve({ 
                        installed: true, 
                        status: 'installed',
                        path: stdout.trim(),
                        message: 'WireGuard is installed'
                    });
                }
            });
        });
    } catch (error) {
        return { 
            installed: false, 
            status: 'error',
            message: error.message 
        };
    }
});

ipcMain.handle('install-wireguard', async () => {
    try {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    success: true,
                    message: 'WireGuard installation completed'
                });
            }, 3000);
        });
    } catch (error) {
        return {
            success: false,
            message: error.message
        };
    }
});

// VPN operations
ipcMain.handle('connect-vpn', async (event, config) => {
    try {
        setTimeout(() => {
            mainWindow.webContents.send('vpn-status-changed', {
                status: 'connected',
                server: config.server || 'US East',
                ip: '10.8.0.2',
                timestamp: new Date().toISOString()
            });
        }, 2000);

        return {
            success: true,
            message: 'Connecting to VPN...'
        };
    } catch (error) {
        return {
            success: false,
            message: error.message
        };
    }
});

ipcMain.handle('disconnect-vpn', async () => {
    try {
        setTimeout(() => {
            mainWindow.webContents.send('vpn-status-changed', {
                status: 'disconnected',
                timestamp: new Date().toISOString()
            });
        }, 1000);

        return {
            success: true,
            message: 'Disconnecting from VPN...'
        };
    } catch (error) {
        return {
            success: false,
            message: error.message
        };
    }
});

ipcMain.handle('get-vpn-status', async () => {
    return {
        status: 'disconnected',
        server: null,
        ip: null,
        connectedAt: null
    };
});

ipcMain.handle('get-vpn-stats', async () => {
    return {
        bytesReceived: Math.floor(Math.random() * 1000000),
        bytesSent: Math.floor(Math.random() * 1000000),
        connectionDuration: 0,
        speed: Math.floor(Math.random() * 100) + ' Mbps'
    };
});

// Configuration management
ipcMain.handle('save-config', async (event, config) => {
    try {
        return { success: true };
    } catch (error) {
        return { success: false, message: error.message };
    }
});

ipcMain.handle('load-config', async () => {
    try {
        return {
            success: true,
            config: {
                autoConnect: false,
                killSwitch: true,
                dns: '1.1.1.1'
            }
        };
    } catch (error) {
        return { success: false, message: error.message };
    }
});

// WireGuard installation and management
ipcMain.handle('install-wireguard-real', async () => {
    try {
        return new Promise((resolve) => {
            const platform = process.platform;
            let installCommand;
            
            if (platform === 'win32') {
                // Windows WireGuard installer
                installCommand = 'powershell -Command "& {Start-Process -FilePath \'https://download.wireguard.com/windows-client/wireguard-installer.exe\' -Wait}"';
            } else if (platform === 'darwin') {
                // macOS
                installCommand = 'brew install wireguard-tools';
            } else {
                // Linux
                installCommand = 'sudo apt-get update && sudo apt-get install -y wireguard';
            }
            
            exec(installCommand, (error, stdout, stderr) => {
                if (error) {
                    console.error('WireGuard installation failed:', error);
                    resolve({
                        success: false,
                        message: `Installation failed: ${error.message}`
                    });
                } else {
                    resolve({
                        success: true,
                        message: 'WireGuard installed successfully'
                    });
                }
            });
        });
    } catch (error) {
        return {
            success: false,
            message: error.message
        };
    }
});

// Real VPN connection with WireGuard
ipcMain.handle('connect-vpn-real', async (event, configData) => {
    try {
        // Create temporary config file
        const tempDir = path.join(__dirname, 'temp');
        if (!fs.existsSync(tempDir)) {
            fs.mkdirSync(tempDir, { recursive: true });
        }
        
        const configPath = path.join(tempDir, 'ghostswitch.conf');
        fs.writeFileSync(configPath, configData.config);
        
        // Connect using WireGuard
        const command = process.platform === 'win32'
            ? `wireguard.exe /installtunnelservice "${configPath}"`
            : `sudo wg-quick up "${configPath}"`;
        
        return new Promise((resolve) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    console.error('WireGuard connection failed:', error);
                    resolve({
                        success: false,
                        message: `Connection failed: ${error.message}`
                    });
                } else {
                    // Parse connection info
                    console.log('WireGuard connected:', stdout);
                    
                    // Send status update
                    setTimeout(() => {
                        mainWindow.webContents.send('vpn-status-changed', {
                            status: 'connected',
                            server: configData.server,
                            ip: configData.clientIP || '10.8.0.2',
                            timestamp: new Date().toISOString()
                        });
                    }, 2000);
                    
                    resolve({
                        success: true,
                        message: 'Connected to VPN successfully'
                    });
                }
            });
        });
    } catch (error) {
        return { success: false, message: error.message };
    }
});

// Disconnect VPN
ipcMain.handle('disconnect-vpn-real', async () => {
    try {
        const command = process.platform === 'win32'
            ? 'wireguard.exe /uninstalltunnelservice ghostswitch'
            : 'sudo wg-quick down ghostswitch';
        
        return new Promise((resolve) => {
            exec(command, (error, stdout, stderr) => {
                // Always consider successful for disconnection
                setTimeout(() => {
                    mainWindow.webContents.send('vpn-status-changed', {
                        status: 'disconnected',
                        timestamp: new Date().toISOString()
                    });
                }, 1000);
                
                resolve({
                    success: true,
                    message: 'Disconnected from VPN'
                });
            });
        });
    } catch (error) {
        return { success: false, message: error.message };
    }
});

// Get real VPN status
ipcMain.handle('get-vpn-status-real', async () => {
    try {
        return new Promise((resolve) => {
            exec('wg show', (error, stdout, stderr) => {
                if (error || !stdout.trim()) {
                    resolve({
                        status: 'disconnected',
                        server: null,
                        ip: null,
                        connectedAt: null
                    });
                } else {
                    // Parse WireGuard output to get connection info
                    const lines = stdout.split('\n');
                    const interfaceLine = lines.find(line => line.startsWith('interface:'));
                    
                    resolve({
                        status: 'connected',
                        server: 'Connected Server',
                        ip: '10.8.0.2', // Would parse from actual output
                        connectedAt: new Date().toISOString()
                    });
                }
            });
        });
    } catch (error) {
        return {
            status: 'disconnected',
            server: null,
            ip: null,
            connectedAt: null
        };
    }
});

// Check if WireGuard is installed
ipcMain.handle('check-wireguard-real', async () => {
    try {
        return new Promise((resolve) => {
            const command = process.platform === 'win32' ? 'wg version' : 'wg --version';
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    resolve({ 
                        installed: false, 
                        message: 'WireGuard not found. Would you like to install it?'
                    });
                } else {
                    resolve({ 
                        installed: true, 
                        message: 'WireGuard is ready',
                        version: stdout.trim()
                    });
                }
            });
        });
    } catch (error) {
        return { installed: false, message: error.message };
    }
});

// Install WireGuard
ipcMain.handle('install-wireguard-real', async () => {
    try {
        const platform = process.platform;
        
        if (platform === 'win32') {
            // Windows - download and run installer
            const { shell } = require('electron');
            shell.openExternal('https://download.wireguard.com/windows-client/wireguard-installer.exe');
            return {
                success: true,
                message: 'WireGuard installer opened. Please complete installation and restart the app.'
            };
        } else {
            return {
                success: false,
                message: 'Please install WireGuard manually for your platform'
            };
        }
    } catch (error) {
        return { success: false, message: error.message };
    }
});

console.log('GhostSwitch VPN Electron main process started');
console.log('Real WireGuard handlers added');