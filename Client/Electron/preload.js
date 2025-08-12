const { contextBridge, ipcRenderer } = require('electron');

// Expose secure APIs to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // App information
    getAppVersion: () => ipcRenderer.invoke('app-version'),

    // WireGuard operations
    checkWireGuard: () => ipcRenderer.invoke('check-wireguard'),
    installWireGuard: () => ipcRenderer.invoke('install-wireguard'),

    // Real WireGuard operations
    installWireGuardReal: () => ipcRenderer.invoke('install-wireguard-real'),

    // VPN operations
    connectVPN: (config) => ipcRenderer.invoke('connect-vpn', config),
    disconnectVPN: () => ipcRenderer.invoke('disconnect-vpn'),
    getVPNStatus: () => ipcRenderer.invoke('get-vpn-status'),
    getVPNStats: () => ipcRenderer.invoke('get-vpn-stats'),

    // Real VPN operations
    connectVPNReal: (config) => ipcRenderer.invoke('connect-vpn-real', config),
    disconnectVPNReal: () => ipcRenderer.invoke('disconnect-vpn-real'),
    getVPNStatusReal: () => ipcRenderer.invoke('get-vpn-status-real'),

    // Configuration
    saveConfig: (config) => ipcRenderer.invoke('save-config', config),
    loadConfig: () => ipcRenderer.invoke('load-config'),

    // Event listeners
    onVPNStatusChanged: (callback) => {
        ipcRenderer.on('vpn-status-changed', (event, data) => callback(data));
    },
    
    onVPNStatsUpdated: (callback) => {
        ipcRenderer.on('vpn-stats-updated', (event, data) => callback(data));
    },

    // Remove listeners
    removeVPNStatusListener: () => {
        ipcRenderer.removeAllListeners('vpn-status-changed');
    },
    
    removeVPNStatsListener: () => {
        ipcRenderer.removeAllListeners('vpn-stats-updated');
    }
});

console.log('Preload script loaded - ElectronAPI exposed');