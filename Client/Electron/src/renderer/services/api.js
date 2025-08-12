import { APP_CONFIG } from '../../shared/constants.js';

class APIService {
    constructor() {
        this.baseURL = APP_CONFIG.API_BASE_URL;
        this.timeout = APP_CONFIG.API_TIMEOUT;
        this.token = null;
    }

    // Set authentication token
    setToken(token) {
        this.token = token;
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` })
            }
        };

        const config = { ...defaultOptions, ...options };
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Authentication methods
    async login(username, password) {
        return this.request('/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    }

    async signup(username, password) {
        return this.request('/register', {
            method: 'POST', 
            body: JSON.stringify({ username, password })
        });
    }

    // VPN-specific methods (to be implemented with your backend)
    async getServers() {
        try {
            return this.request('/servers');
        } catch (error) {
            // Return default servers if API fails
            console.warn('Using default servers due to API error:', error);
            return { success: true, servers: APP_CONFIG.DEFAULT_SERVERS };
        }
    }

    async generateVPNConfig(userId) {
        return this.request('/vpn/config', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });
    }

    async getConnectionStats(userId) {
        return this.request(`/stats/${userId}`);
    }

    // Connection logging
    async logConnection(userId, serverEndpoint) {
        return this.request('/vpn/connect', {
            method: 'POST',
            body: JSON.stringify({ 
                user_id: userId, 
                server_endpoint: serverEndpoint,
                timestamp: new Date().toISOString()
            })
        });
    }

    async logDisconnection(userId) {
        return this.request('/vpn/disconnect', {
            method: 'POST',
            body: JSON.stringify({ 
                user_id: userId,
                timestamp: new Date().toISOString()
            })
        });
    }
}

// Create singleton instance
const apiService = new APIService();
export default apiService;