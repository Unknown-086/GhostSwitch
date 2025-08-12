class RealAPIService {
    constructor() {
        this.baseURL = "http://51.112.111.180:5000/api";
        this.timeout = 15000; // Increased timeout
        this.token = null;
    }

    // Set authentication token
    setToken(token) {
        this.token = token;
        // Save token to localStorage
        localStorage.setItem('ghostswitch_token', token);
    }

    // Get stored token
    getToken() {
        if (!this.token) {
            this.token = localStorage.getItem('ghostswitch_token');
        }
        return this.token;
    }

    // Clear token
    clearToken() {
        this.token = null;
        localStorage.removeItem('ghostswitch_token');
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                ...(this.getToken() && { 'Authorization': `Bearer ${this.getToken()}` })
            },
            mode: 'cors', // Enable CORS
        };

        const config = { ...defaultOptions, ...options };
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            console.log(`🌐 API Request: ${options.method || 'GET'} ${url}`);
            
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            console.log(`📡 API Response: ${response.status} ${response.statusText}`);
            
            const responseData = await response.json();
            
            if (!response.ok) {
                throw new Error(responseData.message || responseData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            console.log(`✅ API Success:`, responseData);
            return responseData;
            
        } catch (error) {
            console.error('❌ API Request failed:', error);
            
            // Handle specific errors
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - check your connection');
            }
            
            if (error.message.includes('fetch')) {
                throw new Error('Network error - backend may be offline');
            }
            
            if (error.message.includes('CORS')) {
                throw new Error('CORS error - backend configuration issue');
            }
            
            throw error;
        }
    }

    // Authentication methods
    async login(username, password) {
        try {
            const response = await this.request('/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });

            if (response.token) {
                this.setToken(response.token);
            }

            return {
                success: true,
                user: response.user || { username, id: response.user_id },
                token: response.token,
                message: response.message || 'Login successful'
            };
        } catch (error) {
            return {
                success: false,
                message: error.message || 'Login failed'
            };
        }
    }

    async register(username, password, email = null) {
        try {
            const response = await this.request('/register', {
                method: 'POST',
                body: JSON.stringify({ 
                    username, 
                    password,
                    ...(email && { email })
                })
            });

            return {
                success: true,
                message: response.message || 'Registration successful'
            };
        } catch (error) {
            return {
                success: false,
                message: error.message || 'Registration failed'
            };
        }
    }

    async logout() {
        try {
            if (this.getToken()) {
                await this.request('/logout', { method: 'POST' });
            }
        } catch (error) {
            console.error('Logout API call failed:', error);
        } finally {
            this.clearToken();
        }
    }

    // VPN-specific methods
    async getVPNServers() {
        try {
            const response = await this.request('/vpn/servers');
            return {
                success: true,
                servers: response.servers || []
            };
        } catch (error) {
            console.error('Failed to get VPN servers:', error);
            // Return default servers as fallback
            return {
                success: false,
                message: error.message,
                servers: [
                    {
                        id: 1,
                        name: "US East",
                        location: "New York, USA",
                        endpoint: "us-east.ghostswitch.com:51820",
                        flag: "🇺🇸",
                        ping: "45ms"
                    },
                    {
                        id: 2,
                        name: "US West", 
                        location: "Los Angeles, USA",
                        endpoint: "us-west.ghostswitch.com:51820",
                        flag: "🇺🇸",
                        ping: "32ms"
                    },
                    {
                        id: 3,
                        name: "Europe",
                        location: "London, UK", 
                        endpoint: "eu.ghostswitch.com:51820",
                        flag: "🇬🇧",
                        ping: "67ms"
                    }
                ]
            };
        }
    }

    async generateVPNConfig(userId) {
        try {
            const response = await this.request('/vpn/config', {
                method: 'POST',
                body: JSON.stringify({ user_id: userId })
            });

            return {
                success: true,
                config: response.config,
                message: response.message
            };
        } catch (error) {
            return {
                success: false,
                message: error.message || 'Failed to generate VPN config'
            };
        }
    }

    async logVPNConnection(userId, serverEndpoint) {
        try {
            const response = await this.request('/vpn/connect', {
                method: 'POST',
                body: JSON.stringify({ 
                    user_id: userId, 
                    server_endpoint: serverEndpoint,
                    timestamp: new Date().toISOString()
                })
            });

            return {
                success: true,
                message: response.message
            };
        } catch (error) {
            console.error('Failed to log VPN connection:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    async logVPNDisconnection(userId) {
        try {
            const response = await this.request('/vpn/disconnect', {
                method: 'POST',
                body: JSON.stringify({ 
                    user_id: userId,
                    timestamp: new Date().toISOString()
                })
            });

            return {
                success: true,
                message: response.message
            };
        } catch (error) {
            console.error('Failed to log VPN disconnection:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    async getConnectionStats(userId) {
        try {
            const response = await this.request(`/stats/${userId}`);
            return {
                success: true,
                stats: response.stats
            };
        } catch (error) {
            console.error('Failed to get connection stats:', error);
            return {
                success: false,
                stats: {
                    bytesReceived: 0,
                    bytesSent: 0,
                    connectionDuration: 0,
                    lastConnected: null
                }
            };
        }
    }

    // Test connection to your backend
    async testConnection() {
        try {
            // Try a simple endpoint first
            const response = await this.request('/health', { method: 'GET' });
            return {
                success: true,
                message: 'Backend connection successful',
                data: response
            };
        } catch (error) {
            console.error('Backend test failed:', error);
            return {
                success: false,
                message: `Backend offline: ${error.message}`
            };
        }
    }
}

// Create singleton instance
const realAPI = new RealAPIService();

// Make it available globally
window.realAPI = realAPI;

console.log('Real API Service loaded - Backend:', realAPI.baseURL);