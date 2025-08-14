const { contextBridge, ipcRenderer } = require('electron');

console.log('🔌 Preload script starting...');

// Expose only Electron APIs to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // App information
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    getAppPath: () => ipcRenderer.invoke('get-app-path'),

    // VPN status
    getVPNStatus: () => ipcRenderer.invoke('get-vpn-status'),

    // VPN status listener
    onVPNStatusChanged: (callback) => {
        ipcRenderer.on('vpn-status-changed', (event, data) => callback(data));
        return () => {
            ipcRenderer.removeAllListeners('vpn-status-changed');
        };
    },

    // WireGuard detection and management
    checkWireGuard: () => ipcRenderer.invoke('check-wireguard'),
    checkWireGuardAdvanced: () => ipcRenderer.invoke('check-wireguard-advanced'),
    downloadWireGuard: () => ipcRenderer.invoke('download-wireguard'),
    installWireGuardSilent: () => ipcRenderer.invoke('install-wireguard-silent'),
    clearWireGuardConfigs: () => ipcRenderer.invoke('clear-wireguard-configs'),

    // VPN connection
    connectVPNReal: (config) => ipcRenderer.invoke('connect-vpn-real', config),
    disconnectVPNReal: () => ipcRenderer.invoke('disconnect-vpn-real'),
    connectVPN: (configPath) => ipcRenderer.invoke('connect-vpn', configPath),
    disconnectVPN: () => ipcRenderer.invoke('disconnect-vpn'),
    checkVPNStatus: () => ipcRenderer.invoke('check-vpn-status'),

    // Utility functions
    openExternal: (url) => ipcRenderer.invoke('open-external', url),

    // System information
    getPlatform: () => process.platform,
    getNodeVersion: () => process.version,

    // Config management
    saveConfigToFile: (configContent) => ipcRenderer.invoke('save-config-to-file', configContent)
});

console.log('✅ Preload script loaded - Electron APIs exposed');