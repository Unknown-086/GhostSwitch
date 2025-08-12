export const APP_CONFIG = {
    // API Configuration
    API_BASE_URL: "http://51.112.111.180:5000/api",
    API_TIMEOUT: 10000,
    
    // Window Configuration
    WINDOW_TITLE: "GhostSwitch VPN",
    
    // VPN Configuration
    DEFAULT_DNS: "1.1.1.1,8.8.8.8",
    KEEPALIVE_INTERVAL: 25,
    
    // Connection States
    VPN_STATUS: {
        DISCONNECTED: 'disconnected',
        CONNECTING: 'connecting',
        CONNECTED: 'connected',
        DISCONNECTING: 'disconnecting',
        ERROR: 'error'
    },
    
    // WireGuard Status
    WIREGUARD_STATUS: {
        CHECKING: 'checking',
        NOT_INSTALLED: 'not_installed',
        INSTALLED: 'installed',
        INSTALLING: 'installing',
        ERROR: 'error'
    },
    
    // Default Servers
    DEFAULT_SERVERS: [
        {
            id: 1,
            name: "US East",
            location: "New York, USA",
            endpoint: "us-east.example.com:51820",
            flag: "🇺🇸",
            ping: "45ms"
        },
        {
            id: 2,
            name: "US West", 
            location: "Los Angeles, USA",
            endpoint: "us-west.example.com:51820",
            flag: "🇺🇸",
            ping: "32ms"
        },
        {
            id: 3,
            name: "Europe",
            location: "London, UK", 
            endpoint: "eu.example.com:51820",
            flag: "🇬🇧",
            ping: "67ms"
        }
    ]
};

export const UI_MESSAGES = {
    // Authentication
    LOGIN_SUCCESS: "Login successful!",
    LOGIN_FAILED: "Login failed. Please check your credentials.",
    SIGNUP_SUCCESS: "Account created successfully!",
    SIGNUP_FAILED: "Registration failed. Please try again.",
    
    // VPN Connection
    CONNECTING: "Connecting to VPN...",
    CONNECTED: "Connected successfully!",
    DISCONNECTING: "Disconnecting...",
    DISCONNECTED: "Disconnected from VPN",
    CONNECTION_ERROR: "Connection failed. Please try again.",
    
    // WireGuard
    WIREGUARD_CHECKING: "Checking WireGuard installation...",
    WIREGUARD_INSTALLED: "WireGuard is installed and ready",
    WIREGUARD_NOT_FOUND: "WireGuard not found on this system",
    WIREGUARD_INSTALLING: "Installing WireGuard...",
    WIREGUARD_INSTALL_SUCCESS: "WireGuard installed successfully!",
    WIREGUARD_INSTALL_FAILED: "Failed to install WireGuard",
    
    // General
    LOADING: "Loading...",
    ERROR: "An error occurred",
    SUCCESS: "Operation completed successfully"
};