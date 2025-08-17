class RealAPIService {
    constructor() {
        this.baseURL = 'http://51.112.215.253:5000/api';
        this.token = this.getToken();
        console.log('Real API Service initialized - Backend:', this.baseURL);
    }

    // Set authentication token
    setToken(token) {
        this.token = token;
        localStorage.setItem('authToken', token);
        console.log('🔑 Auth token stored');
    }

    // Get stored token
    getToken() {
        return localStorage.getItem('authToken');
    }

    // Clear token
    clearToken() {
        this.token = null;
        localStorage.removeItem('authToken');
        console.log('🔑 Auth token cleared');
    }

    // Make authenticated API request
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add auth token if available
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        console.log('🌐 API Request:', config.method || 'GET', url);

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }
            
            console.log('✅ API Response successful');
            return data;
        } catch (error) {
            console.error('❌ API Request failed:', error);
            throw error;
        }
    }

    // Test backend connection
    async testConnection() {
        try {
            const result = await this.request('/health');
            console.log('🟢 Backend health check passed');
            return {
                success: true,
                message: 'Backend connection successful',
                data: result
            };
        } catch (error) {
            console.error('🔴 Backend health check failed:', error);
            return {
                success: false,
                message: `Backend connection failed: ${error.message}`,
                error: error
            };
        }
    }

    // User authentication
    async login(username, password) {
        try {
            console.log('🔐 Attempting login for user:', username);
            
            // EXCELLENT: Proper error propagation
            const result = await this.request('/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
            
            if (result.success && result.token) {
                this.setToken(result.token);  // ✅ Automatic token management
                console.log('✅ Login successful, token stored');
            }
            
            return result;
        } catch (error) {
            console.error('❌ Login failed:', error);
            throw new Error(`Login failed: ${error.message}`);  // ✅ Meaningful errors
        }
    }

    // User registration
    async register(username, password, email = '') {
        try {
            console.log('📝 Attempting registration for user:', username);
            
            const result = await this.request('/register', {
                method: 'POST',
                body: JSON.stringify({ username, password, email })
            });
            
            console.log('✅ Registration completed');
            return result;
        } catch (error) {
            console.error('❌ Registration failed:', error);
            throw new Error(`Registration failed: ${error.message}`);
        }
    }

    // Generate REAL VPN Configuration
    async generateVPNConfig() {
        try {
            if (!this.token) {
                throw new Error('Not authenticated - please login first');
            }

            console.log('🔧 Requesting real VPN configuration from backend...');
            
            const result = await this.request('/vpn/generate-config', {
                method: 'POST'
            });

            if (result.success) {
                console.log('✅ VPN config generated successfully');
                console.log('📍 Assigned IP:', result.client_ip);
                console.log('📄 Config length:', result.config ? result.config.length : 0);
            }
            
            return result;
        } catch (error) {
            console.error('❌ VPN config generation failed:', error);
            throw new Error(`VPN config generation failed: ${error.message}`);
        }
    }

    // Log VPN Connection
    async logVPNConnection(serverEndpoint) {
        try {
            if (!this.token) {
                console.warn('⚠️ Not authenticated, skipping connection logging');
                return { success: false, message: 'Not authenticated' };
            }

            console.log('📊 Logging VPN connection to:', serverEndpoint);
            
            const result = await this.request('/vpn/connect', {
                method: 'POST',
                body: JSON.stringify({ server_endpoint: serverEndpoint })
            });
            
            console.log('✅ VPN connection logged');
            return result;
        } catch (error) {
            console.warn('⚠️ Failed to log VPN connection:', error.message);
            return { success: false, message: error.message };
        }
    }

    // Log VPN Disconnection
    async logVPNDisconnection() {
        try {
            if (!this.token) {
                console.warn('⚠️ Not authenticated, skipping disconnection logging');
                return { success: false, message: 'Not authenticated' };
            }

            console.log('📊 Logging VPN disconnection');
            
            const result = await this.request('/vpn/disconnect', {
                method: 'POST'
            });
            
            console.log('✅ VPN disconnection logged');
            return result;
        } catch (error) {
            console.warn('⚠️ Failed to log VPN disconnection:', error.message);
            return { success: false, message: error.message };
        }
    }

    // Get VPN servers from backend
    async getVPNServers() {
        try {
            console.log('🌐 Fetching VPN servers from backend...');
            
            const result = await this.request('/servers');
            
            if (result.success) {
                console.log('✅ VPN servers loaded:', result.servers.length, 'servers');
                return result;
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('❌ Failed to load VPN servers:', error);
            throw error;
        }
    }

    // Check if user is authenticated
    isAuthenticated() {
        const authenticated = !!this.token;
        console.log('🔍 Authentication status:', authenticated);
        return authenticated;
    }

    // Get current user info from token
    getCurrentUser() {
        if (!this.token) return null;
        
        try {
            // Decode JWT token (basic decode, don't verify signature on client)
            const payload = JSON.parse(atob(this.token.split('.')[1]));
            return {
                id: payload.user_id,
                username: payload.username,
                exp: payload.exp
            };
        } catch (error) {
            console.error('Failed to decode token:', error);
            return null;
        }
    }

    // Logout
    logout() {
        this.clearToken();
        console.log('👋 User logged out');
    }
}

// Create singleton instance
const realAPI = new RealAPIService();

// Make it available globally
window.realAPI = realAPI;

console.log('🚀 Real API Service loaded - Backend:', realAPI.baseURL);