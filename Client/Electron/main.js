const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { exec, spawn } = require('child_process');
const os = require('os');
const fsPromises = require('fs').promises;

// Handle Squirrel startup (optional - with error handling)
let handleSquirrelEvent = false;
try {
    handleSquirrelEvent = require('electron-squirrel-startup');
} catch (error) {
    console.log('⚠️ electron-squirrel-startup not found, continuing...');
    handleSquirrelEvent = false;
}

if (handleSquirrelEvent) {
    app.quit();
}

let mainWindow;

const createWindow = () => {
    console.log('Creating main window...');
    
    // Create the browser window
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: false,
            preload: path.join(__dirname, 'preload.js'),
            webSecurity: false // Allow local file access for development
        },
        icon: path.join(__dirname, 'public', 'ghostswitch_icon.ico'),
        show: false, // Don't show until ready
        titleBarStyle: 'default',
        autoHideMenuBar: true // Hide menu bar for cleaner look
    });

    // Load the HTML file
    const htmlPath = path.join(__dirname, 'src', 'renderer', 'react-index.html');
    console.log('📁 Loading HTML from:', htmlPath);
    
    // Check if file exists
    if (fs.existsSync(htmlPath)) {
        mainWindow.loadFile(htmlPath);
        console.log('✅ HTML file loaded successfully');
    } else {
        console.error('❌ HTML file not found:', htmlPath);
        
        // Try alternative paths
        const altPaths = [
            path.join(__dirname, 'react-index.html'),
            path.join(__dirname, 'src', 'renderer', 'index.html'),
            path.join(__dirname, 'index.html')
        ];
        
        let found = false;
        for (const altPath of altPaths) {
            if (fs.existsSync(altPath)) {
                mainWindow.loadFile(altPath);
                console.log('✅ HTML file loaded from:', altPath);
                found = true;
                break;
            }
        }
        
        if (!found) {
            console.error('❌ No HTML file found anywhere');
            
            // Create a basic HTML file as fallback
            const fallbackHTML = `
<!DOCTYPE html>
<html>
<head>
    <title>GhostSwitch VPN - Error</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .error-container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            max-width: 500px;
            margin: 0 auto;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>🛡️ GhostSwitch VPN</h1>
        <h2>⚠️ File Not Found</h2>
        <p>Main HTML file is missing. Please check your installation.</p>
        <p>Expected location: src/renderer/react-index.html</p>
        <button onclick="location.reload()">🔄 Retry</button>
    </div>
</body>
</html>`;
            
            const fallbackPath = path.join(__dirname, 'fallback.html');
            fs.writeFileSync(fallbackPath, fallbackHTML);
            mainWindow.loadFile(fallbackPath);
        }
    }

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        console.log('🎉 Window ready to show');
        mainWindow.show();
        
        // Open DevTools in development
        mainWindow.webContents.openDevTools();
        // if (process.env.NODE_ENV === 'development' || process.argv.includes('--dev')) {
        // }
    });

    // Handle window closed
    mainWindow.on('closed', () => {
        mainWindow = null;
        console.log('🔴 Main window closed');
    });

    // Handle web contents crash
    mainWindow.webContents.on('crashed', (event, killed) => {
        console.error('❌ Renderer process crashed:', { killed });
    });

    // Handle unresponsive
    mainWindow.on('unresponsive', () => {
        console.warn('⚠️ Main window became unresponsive');
    });

    // Handle navigation
    mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
        const parsedUrl = new URL(navigationUrl);
        
        if (parsedUrl.origin !== 'file://') {
            event.preventDefault();
            console.log('🔒 Blocked navigation to:', navigationUrl);
        }
    });
};

// ===== UTILITY FUNCTIONS =====

function getDownloadUrl(platform) {
    switch (platform) {
        case 'win32':
            return 'https://download.wireguard.com/windows-client/wireguard-installer.exe';
        case 'darwin':
            return 'https://www.wireguard.com/install/';
        case 'linux':
        default:
            return 'https://www.wireguard.com/install/';
    }
}

function getInstallInstructions(platform) {
    switch (platform) {
        case 'win32':
            return [
                '1. Download the WireGuard installer',
                '2. Run as Administrator',
                '3. Follow the installation wizard',
                '4. Restart GhostSwitch VPN'
            ];
        case 'darwin':
            return [
                '1. Download WireGuard from the Mac App Store',
                '2. Or use Homebrew: brew install wireguard-tools',
                '3. Restart GhostSwitch VPN'
            ];
        case 'linux':
        default:
            return [
                '1. Install via package manager:',
                '   Ubuntu/Debian: sudo apt install wireguard',
                '   CentOS/RHEL: sudo yum install wireguard-tools',
                '2. Restart GhostSwitch VPN'
            ];
    }
}

// Check if the application is running with administrator privileges
function isAdminUser() {
  try {
    // Create a test file in a location that requires admin rights
    const testPath = process.platform === 'win32' 
      ? path.join(os.tmpdir(), 'admin-test.txt') 
      : '/etc/admin-test.txt';
    
    fs.writeFileSync(testPath, 'test', { flag: 'w' });
    fs.unlinkSync(testPath);
    return true;
  } catch (e) {
    return false;
  }
}

// ===== IPC HANDLERS =====

// App version
ipcMain.handle('get-app-version', () => {
    return app.getVersion() || '1.0.0';
});

// Get app path
ipcMain.handle('get-app-path', () => {
    return app.getAppPath();
});

// WireGuard check (single consolidated handler)
ipcMain.handle('check-wireguard', async () => {
    return await checkWireGuardAdvanced();
});

ipcMain.handle('check-wireguard-advanced', async () => {
    return await checkWireGuardAdvanced();
});

// Enhanced WireGuard detection
async function checkWireGuardAdvanced() {
    try {
        console.log('Performing WireGuard detection...');
        
        return new Promise((resolve) => {
            const platform = process.platform;
            let checkCommands = [];
            let installPaths = [];
            
            if (platform === 'win32') {
                checkCommands = [
                    'wg version',
                    'wg.exe version', 
                    '"C:\\Program Files\\WireGuard\\wg.exe" version',
                    '"C:\\Program Files (x86)\\WireGuard\\wg.exe" version'
                ];
                
                installPaths = [
                    'C:\\Program Files\\WireGuard\\wg.exe',
                    'C:\\Program Files (x86)\\WireGuard\\wg.exe',
                    'C:\\Windows\\System32\\wg.exe'
                ];
            } else if (platform === 'darwin') {
                checkCommands = [
                    'wg version',
                    '/usr/local/bin/wg version',
                    '/opt/homebrew/bin/wg version'
                ];
            } else {
                checkCommands = [
                    'wg version',
                    '/usr/bin/wg version',
                    '/usr/local/bin/wg version'
                ];
            }
            
            let commandIndex = 0;
            
            function tryNextCommand() {
                if (commandIndex >= checkCommands.length) {
                    if (platform === 'win32') {
                        checkFilePaths();
                    } else {
                        resolve({
                            installed: false,
                            message: 'WireGuard not found',
                            platform: platform,
                            downloadUrl: getDownloadUrl(platform),
                            installInstructions: getInstallInstructions(platform)
                        });
                    }
                    return;
                }
                
                const command = checkCommands[commandIndex];
                console.log(`Testing command: ${command}`);
                
                exec(command, { timeout: 5000 }, (error, stdout, stderr) => {
                    if (!error && stdout) {
                        resolve({
                            installed: true,
                            version: stdout.trim(),
                            path: command,
                            platform: platform,
                            message: `WireGuard found: ${stdout.trim()}`
                        });
                    } else {
                        commandIndex++;
                        tryNextCommand();
                    }
                });
            }
            
            function checkFilePaths() {
                for (const filePath of installPaths) {
                    if (fs.existsSync(filePath)) {
                        exec(`"${filePath}" version`, (error, stdout, stderr) => {
                            if (!error && stdout) {
                                resolve({
                                    installed: true,
                                    version: stdout.trim(),
                                    path: filePath,
                                    platform: platform,
                                    message: `WireGuard found at: ${filePath}`
                                });
                            } else {
                                resolve({
                                    installed: false,
                                    message: 'WireGuard executable found but not working',
                                    platform: platform,
                                    downloadUrl: getDownloadUrl(platform),
                                    installInstructions: getInstallInstructions(platform)
                                });
                            }
                        });
                        return;
                    }
                }
                
                resolve({
                    installed: false,
                    message: 'WireGuard not installed',
                    platform: platform,
                    downloadUrl: getDownloadUrl(platform),
                    installInstructions: getInstallInstructions(platform)
                });
            }
            
            tryNextCommand();
        });
        
    } catch (error) {
        console.error('WireGuard detection error:', error);
        return {
            installed: false,
            message: `Detection error: ${error.message}`,
            platform: process.platform,
            downloadUrl: getDownloadUrl(process.platform),
            installInstructions: getInstallInstructions(process.platform)
        };
    }
}

// Download WireGuard installer
ipcMain.handle('download-wireguard', async () => {
    try {
        const platform = process.platform;
        const downloadUrl = getDownloadUrl(platform);
        
        console.log(`📥 Opening WireGuard download page for ${platform}...`);
        
        // Open download page in default browser
        await shell.openExternal(downloadUrl);
        
        return {
            success: true,
            message: 'Download page opened in browser',
            url: downloadUrl,
            instructions: getInstallInstructions(platform)
        };
        
    } catch (error) {
        console.error('Failed to open download page:', error);
        return {
            success: false,
            message: `Failed to open download: ${error.message}`
        };
    }
});

// Enhanced MSI installation with proper elevation and error handling
ipcMain.handle('install-wireguard-silent', async () => {
    try {
        console.log('🔽 Starting WireGuard MSI installation...');
        
        const platform = process.platform;
        
        if (platform !== 'win32') {
            return {
                success: false,
                message: 'Silent installation only supported on Windows',
                instructions: getInstallInstructions(platform)
            };
        }
        
        // Use the exact MSI URL
        const msiUrl = 'https://download.wireguard.com/windows-client/wireguard-amd64-0.5.3.msi';
        console.log('📥 Downloading WireGuard MSI from:', msiUrl);
        
        const tempDir = path.join(__dirname, 'temp');
        const msiPath = path.join(tempDir, 'wireguard-amd64-0.5.3.msi');
        
        // Create temp directory
        if (!fs.existsSync(tempDir)) {
            fs.mkdirSync(tempDir, { recursive: true });
        }
        
        console.log('🔄 Downloading MSI file...');
        
        return new Promise((resolve) => {
            // Download with curl
            const downloadCommand = `curl -L "${msiUrl}" -o "${msiPath}" --silent --show-error`;
            
            exec(downloadCommand, { timeout: 180000 }, (downloadError, downloadStdout, downloadStderr) => {
                if (downloadError || !fs.existsSync(msiPath)) {
                    console.error('❌ Download failed:', downloadError);
                    resolve({
                        success: false,
                        message: `Download failed: ${downloadError ? downloadError.message : 'File not found'}`,
                        suggestion: 'Check internet connection or try manual installation'
                    });
                    return;
                }
                
                const stats = fs.statSync(msiPath);
                console.log(`✅ Downloaded ${stats.size} bytes`);
                
                // Try multiple installation methods
                tryInstallationMethods(msiPath, resolve);
            });
        });
        
    } catch (error) {
        console.error('❌ Installation setup error:', error);
        return {
            success: false,
            message: `Installation setup failed: ${error.message}`,
            suggestion: 'Check permissions and try again'
        };
    }
});

// Try multiple installation methods with proper elevation
async function tryInstallationMethods(msiPath, resolve) {
    const installationMethods = [
        () => installWithElevatedMsiexec(msiPath),
        () => installWithPowerShellElevated(msiPath),
        () => installWithStartElevated(msiPath),
        () => installWithBasicMsiexec(msiPath)
    ];
    
    let methodIndex = 0;
    
    function tryNextMethod() {
        if (methodIndex >= installationMethods.length) {
            // All methods failed
            cleanupAndResolve(msiPath, {
                success: false,
                message: 'All installation methods failed',
                suggestion: 'Please try manual installation or run as administrator',
                details: 'MSI Error 1603: Installation failed due to permissions or conflicts'
            }, resolve);
            return;
        }
        
        const currentMethod = installationMethods[methodIndex];
        console.log(`🔄 Trying installation method ${methodIndex + 1}...`);
        
        currentMethod()
            .then(async (result) => {
                if (result.success) {
                    // Installation succeeded, verify
                    setTimeout(async () => {
                        const checkResult = await checkWireGuardAdvanced();
                        
                        cleanupAndResolve(msiPath, {
                            success: checkResult.installed,
                            message: checkResult.installed ? 
                                'WireGuard CLI tools installed successfully' : 
                                'Installation completed but tools not detected',
                            method: `method_${methodIndex + 1}`,
                            version: checkResult.version,
                            path: checkResult.path,
                            installType: 'cli-only',
                            details: result.details
                        }, resolve);
                    }, 5000);
                } else {
                    console.log(`❌ Method ${methodIndex + 1} failed: ${result.message}`);
                    methodIndex++;
                    setTimeout(tryNextMethod, 1000); // Wait 1 second before trying next method
                }
            })
            .catch((error) => {
                console.log(`❌ Method ${methodIndex + 1} error:`, error.message);
                methodIndex++;
                setTimeout(tryNextMethod, 1000);
            });
    }
    
    tryNextMethod();
}

// Method 1: Elevated msiexec with proper parameters
function installWithElevatedMsiexec(msiPath) {
    return new Promise((resolve) => {
        console.log('🛠️ Method 1: Elevated msiexec installation...');
        
        // Use PowerShell to run msiexec elevated
        const elevatedCommand = `powershell -Command "Start-Process msiexec -ArgumentList '/i','${msiPath}','/quiet','/norestart','/l*v','${msiPath}.log' -Verb RunAs -Wait"`;
        
        exec(elevatedCommand, { 
            timeout: 180000,
            windowsHide: true 
        }, (error, stdout, stderr) => {
            if (error) {
                resolve({
                    success: false,
                    message: `Elevated msiexec failed: ${error.message}`,
                    details: stderr
                });
            } else {
                resolve({
                    success: true,
                    message: 'Elevated msiexec completed',
                    details: stdout
                });
            }
        });
    });
}

// Method 2: PowerShell with elevation and detailed logging
function installWithPowerShellElevated(msiPath) {
    return new Promise((resolve) => {
        console.log('🛠️ Method 2: PowerShell elevated installation...');
        
        const psScript = `
        try {
            $logPath = "${msiPath}.ps.log"
            Write-Host "Starting MSI installation with logging..."
            
            $process = Start-Process -FilePath "msiexec.exe" -ArgumentList @(
                "/i", "${msiPath}",
                "/quiet",
                "/norestart", 
                "/l*v", $logPath,
                "REBOOT=ReallySuppress"
            ) -Wait -PassThru -Verb RunAs
            
            Write-Host "Installation process completed with exit code: $($process.ExitCode)"
            
            if ($process.ExitCode -eq 0) {
                Write-Host "Installation successful"
                exit 0
            } else {
                Write-Error "Installation failed with exit code $($process.ExitCode)"
                if (Test-Path $logPath) {
                    $logContent = Get-Content $logPath -Tail 20
                    Write-Host "Last 20 lines of install log:"
                    $logContent | ForEach-Object { Write-Host $_ }
                }
                exit $process.ExitCode
            }
        } catch {
            Write-Error "PowerShell installation error: $($_.Exception.Message)"
            exit 1
        }`;
        
        const command = `powershell -ExecutionPolicy Bypass -Command "${psScript}"`;
        
        exec(command, { 
            timeout: 180000,
            windowsHide: true 
        }, (error, stdout, stderr) => {
            if (error) {
                resolve({
                    success: false,
                    message: `PowerShell elevated installation failed: ${error.message}`,
                    details: stdout + '\n' + stderr
                });
            } else {
                resolve({
                    success: true,
                    message: 'PowerShell elevated installation completed',
                    details: stdout
                });
            }
        });
    });
}

// Method 3: Use runas with start command
function installWithStartElevated(msiPath) {
    return new Promise((resolve) => {
        console.log('🛠️ Method 3: Start command with elevation...');
        
        // Use start command with elevated privileges
        const startCommand = `powershell -Command "& { $p = Start-Process -FilePath 'msiexec' -ArgumentList '/i','${msiPath}','/quiet','/norestart' -Verb RunAs -PassThru -Wait; exit $p.ExitCode }"`;
        
        exec(startCommand, { 
            timeout: 180000,
            windowsHide: true 
        }, (error, stdout, stderr) => {
            if (error && error.code !== 0) {
                resolve({
                    success: false,
                    message: `Start elevated failed: ${error.message}`,
                    details: stderr
                });
            } else {
                resolve({
                    success: true,
                    message: 'Start elevated installation completed',
                    details: stdout
                });
            }
        });
    });
}

// Method 4: Basic msiexec (fallback)
function installWithBasicMsiexec(msiPath) {
    return new Promise((resolve) => {
        console.log('🛠️ Method 4: Basic msiexec installation...');
        
        const basicCommand = `msiexec /i "${msiPath}" /quiet /norestart`;
        
        exec(basicCommand, { 
            timeout: 120000,
            windowsHide: true 
        }, (error, stdout, stderr) => {
            if (error) {
                resolve({
                    success: false,
                    message: `Basic msiexec failed: ${error.message}`,
                    details: stderr
                });
            } else {
                resolve({
                    success: true,
                    message: 'Basic msiexec completed',
                    details: stdout
                });
            }
        });
    });
}

// Cleanup MSI file and resolve
function cleanupAndResolve(msiPath, result, resolve) {
    try {
        // Clean up MSI file
        if (fs.existsSync(msiPath)) {
            fs.unlinkSync(msiPath);
            console.log('🗑️ MSI file cleaned up');
        }
        
        // Clean up log files
        const logFiles = [`${msiPath}.log`, `${msiPath}.ps.log`];
        logFiles.forEach(logFile => {
            if (fs.existsSync(logFile)) {
                try {
                    fs.unlinkSync(logFile);
                    console.log(`🗑️ Log file cleaned up: ${logFile}`);
                } catch (logError) {
                    console.warn(`Failed to clean log file: ${logFile}`);
                }
            }
        });
        
    } catch (cleanupError) {
        console.error('Cleanup error:', cleanupError);
    }
    
    resolve(result);
}

// Clear WireGuard configurations
ipcMain.handle('clear-wireguard-configs', async () => {
    try {
        console.log('🧹 Clearing old WireGuard configurations...');
        
        const tempDir = path.join(__dirname, 'temp');
        let clearedConfigs = [];
        
        if (fs.existsSync(tempDir)) {
            try {
                const files = fs.readdirSync(tempDir);
                
                for (const file of files) {
                    if (file.endsWith('.conf') && file.startsWith('ghostswitch')) {
                        const filePath = path.join(tempDir, file);
                        fs.unlinkSync(filePath);
                        clearedConfigs.push(filePath);
                        console.log(`🗑️ Cleared config: ${filePath}`);
                    }
                }
            } catch (dirError) {
                console.warn(`Failed to clear configs in ${tempDir}:`, dirError.message);
            }
        }
        
        return {
            success: true,
            message: `Cleared ${clearedConfigs.length} old configurations`,
            clearedFiles: clearedConfigs
        };
        
    } catch (error) {
        console.error('Failed to clear configs:', error);
        return {
            success: false,
            message: `Failed to clear configs: ${error.message}`
        };
    }
});

// Get VPN status
ipcMain.handle('get-vpn-status', async () => {
    try {
        return new Promise((resolve) => {
            exec('wg show', { timeout: 5000 }, (error, stdout, stderr) => {
                if (error || !stdout.trim()) {
                    resolve({
                        status: 'disconnected',
                        message: 'No active WireGuard connections'
                    });
                } else {
                    // Parse WireGuard output
                    const lines = stdout.split('\n');
                    const interfaceLine = lines.find(line => line.startsWith('interface:'));
                    
                    if (interfaceLine) {
                        resolve({
                            status: 'connected',
                            interface: interfaceLine.split(': ')[1],
                            details: stdout,
                            message: 'VPN is active'
                        });
                    } else {
                        resolve({
                            status: 'disconnected',
                            message: 'No interface found'
                        });
                    }
                }
            });
        });
    } catch (error) {
        return {
            status: 'error',
            message: error.message
        };
    }
});



// Real VPN connection handler
ipcMain.handle('connect-vpn-real', async (event, connectionData) => {
  try {
    console.log('🚀 Starting REAL WireGuard connection...');
    
    const { server, endpoint, config, clientIP } = connectionData;
    
    // 1. Clear any existing configs
    await clearOldConfigs();
    
    // 2. Create WireGuard config file
    const configPath = await createWireGuardConfig(config);
    
    // 3. Connect using wg-quick
    const connected = await connectWireGuard(configPath);
    
    if (connected) {
      // 4. Verify connection
      const status = await verifyConnection();
      
      if (status.connected) {
        // 5. Update status
        mainWindow.webContents.send('vpn-status-changed', {
          status: 'connected',
          server: server,
          ip: clientIP,
          publicIP: status.publicIP,
          interface: status.interface
        });
        
        return { success: true, message: 'VPN connected successfully', realConnection: true };
      } else {
        throw new Error('Connection verification failed');
      }
    } else {
      throw new Error('WireGuard connection failed');
    }
    
  } catch (error) {
    console.error('❌ VPN connection error:', error);
    
    mainWindow.webContents.send('vpn-status-changed', {
      status: 'disconnected'
    });
    
    return { success: false, message: error.message };
  }
});

// Clear old configurations
async function clearOldConfigs() {
  try {
    const isWindows = process.platform === 'win32';
    
    if (isWindows) {
      // Stop any existing GhostSwitch tunnels
      await new Promise((resolve) => {
        exec('wg-quick down GhostSwitch', { timeout: 10000 }, (error) => {
          resolve(); // Don't fail if no tunnel exists
        });
      });
    } else {
      // Linux/Mac
      await new Promise((resolve) => {
        exec('sudo wg-quick down /etc/wireguard/GhostSwitch.conf', { timeout: 10000 }, (error) => {
          resolve(); // Don't fail if no tunnel exists
        });
      });
    }
  } catch (error) {
    console.log('Old config cleanup completed');
  }
}

// Verify the connection is working
async function verifyConnection() {
  return new Promise((resolve) => {
    // Check if WireGuard interface is up
    exec('wg show', { timeout: 5000 }, (error, stdout, stderr) => {
      if (error || !stdout) {
        resolve({ connected: false });
        return;
      }
      
      // Parse WireGuard output to verify our connection
      const lines = stdout.split('\n');
      const hasInterface = lines.some(line => line.includes('interface'));
      const hasPeer = lines.some(line => line.includes('peer'));
      
      if (hasInterface && hasPeer) {
        // Try to get public IP to verify traffic routing
        exec('curl -s https://api.ipify.org', { timeout: 10000 }, (ipError, ipStdout) => {
          resolve({
            connected: true,
            interface: hasInterface,
            publicIP: ipStdout ? ipStdout.trim() : 'Unknown',
            details: stdout
          });
        });
      } else {
        resolve({ connected: false });
      }
    });
  });
}

// Create WireGuard configuration file - FIXED VERSION
// Create WireGuard configuration file - FIXED VERSION
async function createWireGuardConfig(configContent) {
  try {
    const fsPromises = require('fs').promises;
    
    const configDir = process.platform === 'win32' 
      ? path.join(os.homedir(), 'AppData', 'Local', 'WireGuard', 'Configurations')
      : '/etc/wireguard';
    
    // Ensure directory exists using fsPromises
    try {
      await fsPromises.mkdir(configDir, { recursive: true });
    } catch (dirError) {
      console.log('Directory creation error:', dirError.message);
      // Fallback to synchronous if needed
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
    }
    
    const configPath = path.join(configDir, 'GhostSwitch.conf');
    
    // Write configuration using fsPromises
    await fsPromises.writeFile(configPath, configContent, { mode: 0o600 });
    
    console.log('WireGuard config created:', configPath);
    return configPath;
    
  } catch (error) {
    console.error('Failed to create config:', error);
    throw error;
  }
}

// WireGuard CLI Integration for Windows
const wireguardPath = 'C:\\Program Files\\WireGuard\\wireguard.exe';
const wgPath = 'C:\\Program Files\\WireGuard\\wg.exe';

/**
 * Import and activate a WireGuard tunnel configuration
 * @param {string} configPath - Path to the WireGuard config file
 * @returns {Promise<boolean>} - True if successful
 */
async function connectWireGuard(configPath) {
  return new Promise((resolve, reject) => {
    console.log('🔗 Starting WireGuard connection...');
    console.log(`Config path: ${configPath}`);
    
    if (process.platform === 'win32') {
      // Windows approach using WireGuard CLI
      const tunnelName = 'GhostSwitch';
      
      // First check if tunnel already exists
      exec('sc query WireGuardTunnel$GhostSwitch', (error, stdout) => {
        const tunnelExists = !error && stdout.includes('SERVICE_NAME');
        
        if (tunnelExists) {
          console.log('🔄 Removing existing tunnel configuration...');
          // Remove existing tunnel before creating a new one
          exec(`"${wireguardPath}" /uninstalltunnelservice ${tunnelName}`, (uninstallError) => {
            if (uninstallError) {
              console.warn(`⚠️ Could not remove existing tunnel: ${uninstallError.message}`);
              // Continue anyway - it might not be critical
            }
            
            importAndStartTunnel();
          });
        } else {
          importAndStartTunnel();
        }
      });
      
      function importAndStartTunnel() {
        console.log('📥 Importing tunnel configuration...');
        // Import the tunnel configuration
        exec(`"${wireguardPath}" /installtunnelservice "${configPath}"`, (importError, importStdout, importStderr) => {
          if (importError) {
            console.error('❌ Failed to import WireGuard configuration:', importError);
            console.error('Error output:', importStderr);
            reject(new Error(`Failed to import WireGuard configuration: ${importError.message}`));
            return;
          }
          
          console.log('✅ WireGuard configuration imported successfully');
          
          // Start the tunnel
          console.log('▶️ Starting WireGuard tunnel...');
          exec(`"${wireguardPath}" /tunnel GhostSwitch /start`, (startError, startStdout, startStderr) => {
            if (startError) {
              console.error('❌ Failed to start WireGuard tunnel:', startError);
              console.error('Error output:', startStderr);
              reject(new Error(`Failed to start WireGuard tunnel: ${startError.message}`));
              return;
            }
            
            console.log('✅ WireGuard tunnel started successfully');
            
            // Verify connection by checking interface status
            setTimeout(() => {
              exec(`"${wgPath}" show`, (showError, showStdout) => {
                if (showError || !showStdout.includes('interface')) {
                  console.warn('⚠️ WireGuard interface not detected');
                  // Still resolve since tunnel service might be starting
                  resolve(true);
                  return;
                }
                
                console.log('✅ WireGuard interface active');
                resolve(true);
              });
            }, 2000);
          });
        });
      }
    } else {
      // Unix approach (Linux/Mac)
      console.log('🔗 Using Unix WireGuard approach');
      const command = 'sudo';
      const args = ['wg-quick', 'up', configPath];
      
      const wgProcess = spawn(command, args, { stdio: 'pipe' });
      
      wgProcess.stdout.on('data', (data) => {
        console.log(`WireGuard: ${data.toString().trim()}`);
      });
      
      wgProcess.stderr.on('data', (data) => {
        console.error(`WireGuard Error: ${data.toString().trim()}`);
      });
      
      wgProcess.on('close', (code) => {
        if (code === 0) {
          console.log('✅ WireGuard connected successfully');
          resolve(true);
        } else {
          console.error('❌ WireGuard connection failed with code:', code);
          reject(new Error(`WireGuard failed with code ${code}`));
        }
      });
    }
  });
}

/**
 * Disconnect from WireGuard tunnel
 * @returns {Promise<boolean>} - True if successful
 */
async function disconnectWireGuard() {
  return new Promise((resolve, reject) => {
    console.log('🔌 Disconnecting from WireGuard...');
    
    if (process.platform === 'win32') {
      // Windows approach using WireGuard CLI
      console.log('🛑 Stopping WireGuard tunnel...');
      exec(`"${wireguardPath}" /tunnel GhostSwitch /stop`, (stopError) => {
        if (stopError) {
          console.warn(`⚠️ Could not stop tunnel: ${stopError.message}`);
          // Try uninstalling anyway
        }
        
        console.log('🗑️ Removing WireGuard tunnel...');
        exec(`"${wireguardPath}" /uninstalltunnelservice GhostSwitch`, (uninstallError) => {
          if (uninstallError) {
            console.error('❌ Failed to remove WireGuard tunnel:', uninstallError);
            reject(new Error(`Failed to remove WireGuard tunnel: ${uninstallError.message}`));
            return;
          }
          
          console.log('✅ WireGuard tunnel removed successfully');
          resolve(true);
        });
      });
    } else {
      // Unix approach
      const command = 'sudo';
      const args = ['wg-quick', 'down', 'wg0'];
      
      const wgProcess = spawn(command, args);
      
      wgProcess.on('close', (code) => {
        if (code === 0) {
          console.log('✅ WireGuard disconnected successfully');
          resolve(true);
        } else {
          console.error('❌ WireGuard disconnection failed with code:', code);
          reject(new Error(`WireGuard disconnection failed with code ${code}`));
        }
      });
    }
  });
}

/**
 * Check if WireGuard tunnel is active
 * @returns {Promise<boolean>} - True if active
 */
async function isWireGuardActive() {
  return new Promise((resolve) => {
    if (process.platform === 'win32') {
      // Check if the tunnel service is running
      exec('sc query WireGuardTunnel$GhostSwitch', (error, stdout) => {
        if (error || !stdout.includes('RUNNING')) {
          resolve(false);
          return;
        }
        
        // Also check if the interface is actually active
        exec(`"${wgPath}" show`, (wgError, wgStdout) => {
          resolve(!wgError && wgStdout.includes('interface'));
        });
      });
    } else {
      // Unix approach
      exec('wg', (error, stdout) => {
        resolve(!error && stdout.trim().length > 0);
      });
    }
  });
}

// Add these IPC handlers

// Save WireGuard config to file
ipcMain.handle('save-config-to-file', async (event, configContent) => {
  try {
    const configDir = path.join(os.homedir(), 'AppData', 'Local', 'WireGuard', 'Configurations');
    
    // Create directory if it doesn't exist
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
    
    // Write config file
    const configPath = path.join(configDir, 'GhostSwitch.conf');
    fs.writeFileSync(configPath, configContent);
    
    console.log(`✅ WireGuard config created: ${configPath}`);
    return configPath;
  } catch (error) {
    console.error('❌ Failed to save config file:', error);
    throw error;
  }
});

// Connect to VPN
ipcMain.handle('connect-vpn', async (event, configPath) => {
  try {
    await connectWireGuard(configPath);
    return { success: true };
  } catch (error) {
    console.error('❌ VPN connection error:', error);
    return { success: false, error: error.message };
  }
});

// Disconnect VPN
ipcMain.handle('disconnect-vpn', async () => {
  try {
    await disconnectWireGuard();
    return { success: true };
  } catch (error) {
    console.error('❌ VPN disconnection error:', error);
    return { success: false, error: error.message };
  }
});

// Check VPN status
ipcMain.handle('check-vpn-status', async () => {
  try {
    const isActive = await isWireGuardActive();
    return { isActive };
  } catch (error) {
    console.error('❌ VPN status check error:', error);
    return { isActive: false, error: error.message };
  }
});


// ===== APP EVENT HANDLERS =====

app.whenReady().then(() => {
    console.log('Electron app is ready');
    console.log('App path:', app.getAppPath());
    console.log('User data path:', app.getPath('userData'));
    
    // Check if we're running as admin
    const isAdmin = isAdminUser();
    console.log(`Running with${isAdmin ? '' : 'out'} administrative privileges`);
    
    if (process.platform === 'win32' && !isAdmin) {
        // If not admin on Windows, we'll need to warn the user
        console.log('VPN functionality will be limited without admin privileges');
    }
    
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    console.log('All windows closed');
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// Handle certificate errors
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
    if (url.startsWith('https://51.112.111.180')) {
        // Allow your backend server's self-signed certificate
        event.preventDefault();
        callback(true);
    } else {
        callback(false);
    }
});

// Prevent new window creation
app.on('web-contents-created', (event, contents) => {
    contents.on('new-window', (event, navigationUrl) => {
        event.preventDefault();
        shell.openExternal(navigationUrl);
    });
});

console.log('Main process initialized');
console.log('Node version:', process.version);
console.log('Electron version:', process.versions.electron);