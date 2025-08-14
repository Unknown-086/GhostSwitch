# import subprocess
# import os
# import platform
# import tempfile
# from pathlib import Path

# class WireGuardManager:
#     def __init__(self):
#         self.system = platform.system()
#         self.wireguard_path = self.detect_wireguard()
        
#     def detect_wireguard(self):
#         """Detect if WireGuard is installed and return path"""
#         if self.system == "Windows":
#             # Common WireGuard installation paths on Windows
#             possible_paths = [
#                 r"C:\Program Files\WireGuard\wg.exe",
#                 r"C:\Program Files (x86)\WireGuard\wg.exe",
#                 os.path.expanduser(r"~\AppData\Local\WireGuard\wg.exe")
#             ]
            
#             for path in possible_paths:
#                 if os.path.exists(path):
#                     return path
                    
#             # Try to find in PATH
#             try:
#                 result = subprocess.run(["where", "wg"], 
#                                       capture_output=True, text=True, check=True)
#                 return result.stdout.strip().split('\n')[0]
#             except subprocess.CalledProcessError:
#                 return None
                
#         elif self.system == "Linux":
#             try:
#                 result = subprocess.run(["which", "wg"], 
#                                       capture_output=True, text=True, check=True)
#                 return result.stdout.strip()
#             except subprocess.CalledProcessError:
#                 return None
                
#         return None
    
#     def is_installed(self):
#         """Check if WireGuard is properly installed"""
#         return self.wireguard_path is not None
    
#     def get_installation_url(self):
#         """Get the appropriate download URL for the current system"""
#         if self.system == "Windows":
#             return "https://download.wireguard.com/windows-client/"
#         elif self.system == "Linux":
#             return "https://www.wireguard.com/install/"
#         else:
#             return "https://www.wireguard.com/install/"
    
#     def create_tunnel(self, config_content, tunnel_name="GhostSwitch"):
#         """Create a WireGuard tunnel with the given configuration"""
#         if not self.is_installed():
#             raise Exception("WireGuard is not installed")
            
#         # Implementation depends on the system
#         if self.system == "Windows":
#             return self._create_tunnel_windows(config_content, tunnel_name)
#         elif self.system == "Linux":
#             return self._create_tunnel_linux(config_content, tunnel_name)
    
#     def _create_tunnel_windows(self, config_content, tunnel_name):
#         """Create tunnel on Windows using WireGuard GUI"""
#         # Save config to temp file
#         config_dir = Path.home() / "AppData" / "Local" / "GhostSwitch"
#         config_dir.mkdir(exist_ok=True)
        
#         config_file = config_dir / f"{tunnel_name}.conf"
#         with open(config_file, 'w') as f:
#             f.write(config_content)
            
#         return str(config_file)
    
#     def connect_tunnel(self, tunnel_name="GhostSwitch"):
#         """Connect to the specified tunnel"""
#         if self.system == "Windows":
#             # Use WireGuard CLI or GUI automation
#             try:
#                 subprocess.run([
#                     "powershell", "-Command", 
#                     f"Start-Process -FilePath 'wireguard' -ArgumentList '/installtunnelservice {tunnel_name}.conf'"
#                 ], check=True)
#                 return True
#             except subprocess.CalledProcessError:
#                 return False
                
#     def disconnect_tunnel(self, tunnel_name="GhostSwitch"):
#         """Disconnect from the specified tunnel"""
#         if self.system == "Windows":
#             try:
#                 subprocess.run([
#                     "powershell", "-Command", 
#                     f"Stop-Service -Name 'WireGuardTunnel${tunnel_name}'"
#                 ], check=True)
#                 return True
#             except subprocess.CalledProcessError:
#                 return False
    
#     def get_tunnel_status(self, tunnel_name="GhostSwitch"):
#         """Get the current status of the tunnel"""
#         try:
#             if self.system == "Windows":
#                 result = subprocess.run([
#                     "powershell", "-Command",
#                     f"Get-Service -Name 'WireGuardTunnel${tunnel_name}' -ErrorAction SilentlyContinue"
#                 ], capture_output=True, text=True)
                
#                 if "Running" in result.stdout:
#                     return "connected"
#                 elif "Stopped" in result.stdout:
#                     return "disconnected"
#                 else:
#                     return "not_configured"
#         except:
#             pass
            
#         return "unknown"




import subprocess
import os
import platform
import tempfile
from pathlib import Path

class WireGuardManager:
    def __init__(self):
        self.system = platform.system()
        self.config_path = None
        
    def is_installed(self):
        """Check if WireGuard is properly installed"""
        try:
            if self.system == "Windows":
                result = subprocess.run(["where", "wg"], capture_output=True, text=True)
                return result.returncode == 0
            else:
                result = subprocess.run(["which", "wg"], capture_output=True, text=True)
                return result.returncode == 0
        except:
            return False
        
    def create_config_file(self, config_content, tunnel_name="GhostSwitch"):
        """Create WireGuard configuration file"""
        try:
            if self.system == "Windows":
                # Windows WireGuard config directory
                config_dir = os.path.expanduser("~/AppData/Local/WireGuard/Configurations")
            else:
                # Linux WireGuard config directory
                config_dir = "/etc/wireguard"
                
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, f"{tunnel_name}.conf")
            
            with open(config_file, 'w') as f:
                f.write(config_content)
                
            # Set proper permissions (important for WireGuard)
            os.chmod(config_file, 0o600)
            
            self.config_path = config_file
            return config_file
            
        except Exception as e:
            print(f"Failed to create config file: {e}")
            return None
    
    def connect_tunnel(self, tunnel_name="GhostSwitch"):
        """Actually connect to WireGuard tunnel"""
        try:
            if not self.config_path:
                raise Exception("No configuration file created")
                
            if self.system == "Windows":
                # Use WireGuard Windows client
                cmd = ["wg-quick", "up", self.config_path]
            else:
                # Use WireGuard Linux
                cmd = ["sudo", "wg-quick", "up", f"/etc/wireguard/{tunnel_name}.conf"]
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("WireGuard tunnel connected successfully")
                return True
            else:
                print(f"WireGuard connection failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Failed to connect tunnel: {e}")
            return False
    
    def disconnect_tunnel(self, tunnel_name="GhostSwitch"):
        """Disconnect WireGuard tunnel"""
        try:
            if self.system == "Windows":
                cmd = ["wg-quick", "down", self.config_path]
            else:
                cmd = ["sudo", "wg-quick", "down", f"/etc/wireguard/{tunnel_name}.conf"]
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("WireGuard tunnel disconnected successfully")
                return True
            else:
                print(f"WireGuard disconnection failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Failed to disconnect tunnel: {e}")
            return False
    
    def get_tunnel_status(self, tunnel_name="GhostSwitch"):
        """Get actual tunnel status"""
        try:
            result = subprocess.run(["wg", "show"], capture_output=True, text=True)
            
            if result.returncode == 0 and tunnel_name.lower() in result.stdout.lower():
                return "connected"
            else:
                return "disconnected"
                
        except Exception as e:
            print(f"Failed to get tunnel status: {e}")
            return "unknown"
    
    def add_route_rules(self):
        """Add routing rules to ensure all traffic goes through VPN"""
        try:
            if self.system == "Windows":
                # Add route to send all traffic through VPN interface
                subprocess.run(["route", "add", "0.0.0.0", "mask", "0.0.0.0", "10.0.0.1"], 
                             capture_output=True)
            else:
                # Linux routing
                subprocess.run(["sudo", "ip", "route", "add", "default", "via", "10.0.0.1"], 
                             capture_output=True)
                
            return True
        except:
            return False