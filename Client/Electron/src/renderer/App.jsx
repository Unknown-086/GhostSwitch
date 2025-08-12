import React, { useState, useEffect } from 'react';
import LoginPage from './components/LoginPage.jsx';
import VPNDashboard from './components/VPNDashboard.jsx';
import './App.css';

const App = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [vpnStatus, setVpnStatus] = useState('disconnected');
    const [wireGuardStatus, setWireGuardStatus] = useState('checking');

    // Check authentication and system status on startup
    useEffect(() => {
        initializeApp();
    }, []);

    const initializeApp = async () => {
        try {
            setIsLoading(true);
            
            // Check if user is already logged in (check local storage)
            const savedUser = localStorage.getItem('ghostswitch_user');
            if (savedUser) {
                setUser(JSON.parse(savedUser));
                setIsAuthenticated(true);
            }

            // Check WireGuard installation
            await checkWireGuardStatus();

            // Get initial VPN status
            await checkVPNStatus();

        } catch (error) {
            console.error('App initialization failed:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const checkWireGuardStatus = async () => {
        try {
            if (window.electronAPI) {
                const result = await window.electronAPI.checkWireGuard();
                setWireGuardStatus(result.installed ? 'installed' : 'not_installed');
            }
        } catch (error) {
            console.error('WireGuard check failed:', error);
            setWireGuardStatus('error');
        }
    };

    const checkVPNStatus = async () => {
        try {
            if (window.electronAPI) {
                const status = await window.electronAPI.getVPNStatus();
                setVpnStatus(status.status);
            }
        } catch (error) {
            console.error('VPN status check failed:', error);
        }
    };

    const handleLogin = async (username, password) => {
        try {
            setIsLoading(true);
            
            // Here you would normally call your API
            // For now, we'll simulate a successful login
            const userData = {
                id: 1,
                username: username,
                email: `${username}@example.com`,
                loginTime: new Date().toISOString()
            };

            // Save user data
            localStorage.setItem('ghostswitch_user', JSON.stringify(userData));
            setUser(userData);
            setIsAuthenticated(true);

            return { success: true, message: 'Login successful!' };
        } catch (error) {
            console.error('Login failed:', error);
            return { success: false, message: 'Login failed. Please try again.' };
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('ghostswitch_user');
        setUser(null);
        setIsAuthenticated(false);
        setVpnStatus('disconnected');
    };

    const handleVPNConnect = async (server) => {
        try {
            if (window.electronAPI) {
                const result = await window.electronAPI.connectVPN({
                    server: server.name,
                    endpoint: server.endpoint
                });
                
                if (result.success) {
                    setVpnStatus('connecting');
                    return { success: true, message: 'Connecting to VPN...' };
                } else {
                    return { success: false, message: result.message };
                }
            }
        } catch (error) {
            console.error('VPN connection failed:', error);
            return { success: false, message: 'Connection failed' };
        }
    };

    const handleVPNDisconnect = async () => {
        try {
            if (window.electronAPI) {
                const result = await window.electronAPI.disconnectVPN();
                
                if (result.success) {
                    setVpnStatus('disconnecting');
                    return { success: true, message: 'Disconnecting...' };
                } else {
                    return { success: false, message: result.message };
                }
            }
        } catch (error) {
            console.error('VPN disconnection failed:', error);
            return { success: false, message: 'Disconnection failed' };
        }
    };

    // Set up VPN status listener
    useEffect(() => {
        if (window.electronAPI && window.electronAPI.onVPNStatusChanged) {
            window.electronAPI.onVPNStatusChanged((statusData) => {
                setVpnStatus(statusData.status);
            });
        }
    }, []);

    if (isLoading) {
        return (
            <div className="app-loading">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <h2>🛡️ GhostSwitch VPN</h2>
                    <p>Initializing secure connection...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="app">
            {!isAuthenticated ? (
                <LoginPage 
                    onLogin={handleLogin}
                    isLoading={isLoading}
                />
            ) : (
                <VPNDashboard 
                    user={user}
                    vpnStatus={vpnStatus}
                    wireGuardStatus={wireGuardStatus}
                    onConnect={handleVPNConnect}
                    onDisconnect={handleVPNDisconnect}
                    onLogout={handleLogout}
                    onRefreshWireGuard={checkWireGuardStatus}
                />
            )}
        </div>
    );
};

export default App;