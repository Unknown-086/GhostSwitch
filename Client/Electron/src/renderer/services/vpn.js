import { APP_CONFIG, UI_MESSAGES } from '../../shared/constants.js';
import apiService from './api.js';

class VPNService {
    constructor() {
        this.status = APP_CONFIG.VPN_STATUS.DISCONNECTED;
        this.currentServer = null;
        this.connectionStartTime = null;
        this.stats = {
            bytesReceived: 0,
            bytesSent: 0,
            connectionDuration: 0,
            speed: '0 Mbps'
        };
        
        // Event listeners for real-time updates
        this.statusListeners = [];
        this.statsListeners = [];
        
        // Set up Electron IPC listeners
        this.setupEventListeners();
    }

    // Set up event listeners for Electron IPC
    setupEventListeners() {
        if (window.electronAPI) {
            // Listen for VPN status changes from main process
            window.electronAPI.onVPNStatusChanged((statusData) => {
                this.status = statusData.status;
                if (statusData.status === APP_CONFIG.VPN_STATUS.CONNECTED) {
                    this.currentServer = statusData.server;
                    this.connectionStartTime = new Date(statusData.timestamp);
                } else {
                    this.currentServer = null;
                    this.connectionStartTime = null;
                }
                this.notifyStatusListeners(statusData);
            });

            // Listen for stats updates
            window.electronAPI.onVPNStatsUpdated((statsData) => {
                this.stats = { ...this.stats, ...statsData };
                this.notifyStatsListeners(this.stats);
            });
        }
    }

    // Status management
    onStatusChange(callback) {
        this.statusListeners.push(callback);
        return () => {
            this.statusListeners = this.statusListeners.filter(cb => cb !== callback);
        };
    }

    onStatsUpdate(callback) {
        this.statsListeners.push(callback);
        return () => {
            this.statsListeners = this.statsListeners.filter(cb => cb !== callback);
        };
    }

    notifyStatusListeners(statusData) {
        this.statusListeners.forEach(callback => callback(statusData));
    }

    notifyStatsListeners(statsData) {
        this.statsListeners.forEach(callback => callback(statsData));
    }

    // VPN Operations
    async connect(server, userId) {
        try {
            this.status = APP_CONFIG.VPN_STATUS.CONNECTING;
            this.notifyStatusListeners({ 
                status: this.status, 
                message: UI_MESSAGES.CONNECTING 
            });

            // Get VPN configuration from your API
            const configResponse = await apiService.generateVPNConfig(userId);
            
            if (!configResponse.success) {
                throw new Error('Failed to get VPN configuration');
            }

            // Connect via Electron
            const result = await window.electronAPI.connectVPN({
                server: server.name,
                config: configResponse.config
            });

            if (result.success) {
                // Log connection to your API
                await apiService.logConnection(userId, server.endpoint);
                return { success: true, message: UI_MESSAGES.CONNECTING };
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            this.status = APP_CONFIG.VPN_STATUS.ERROR;
            this.notifyStatusListeners({ 
                status: this.status, 
                message: error.message 
            });
            return { success: false, message: error.message };
        }
    }

    async disconnect(userId) {
        try {
            this.status = APP_CONFIG.VPN_STATUS.DISCONNECTING;
            this.notifyStatusListeners({ 
                status: this.status, 
                message: UI_MESSAGES.DISCONNECTING 
            });

            const result = await window.electronAPI.disconnectVPN();
            
            if (result.success) {
                // Log disconnection to your API
                if (userId) {
                    await apiService.logDisconnection(userId);
                }
                return { success: true, message: UI_MESSAGES.DISCONNECTING };
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            this.status = APP_CONFIG.VPN_STATUS.ERROR;
            this.notifyStatusListeners({ 
                status: this.status, 
                message: error.message 
            });
            return { success: false, message: error.message };
        }
    }

    async getStatus() {
        try {
            const status = await window.electronAPI.getVPNStatus();
            this.status = status.status;
            return status;
        } catch (error) {
            console.error('Failed to get VPN status:', error);
            return { status: APP_CONFIG.VPN_STATUS.ERROR };
        }
    }

    async getStats() {
        try {
            const stats = await window.electronAPI.getVPNStats();
            this.stats = { ...this.stats, ...stats };
            return this.stats;
        } catch (error) {
            console.error('Failed to get VPN stats:', error);
            return this.stats;
        }
    }

    // Server management
    async getAvailableServers() {
        try {
            const response = await apiService.getServers();
            return response.servers || APP_CONFIG.DEFAULT_SERVERS;
        } catch (error) {
            console.error('Failed to get servers:', error);
            return APP_CONFIG.DEFAULT_SERVERS;
        }
    }

    // Utility methods
    getConnectionDuration() {
        if (!this.connectionStartTime) return 0;
        return Math.floor((Date.now() - this.connectionStartTime.getTime()) / 1000);
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Create singleton instance
const vpnService = new VPNService();
export default vpnService;