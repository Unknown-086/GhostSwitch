#!/bin/bash

# WireGuard Installation Script

set -e  # Exit immediately if a command exits with non-zero status

# Updating the package list and upgrading the packages
sudo apt update
sudo apt upgrade -y
sudo apt install net-tools

# Installing WireGuard
sudo apt install wireguard -y

# Creating the WireGuard configuration directory
# Create directory with proper permissions
sudo mkdir -p /etc/wireguard
cd /etc/wireguard
sudo chmod 700 /etc/wireguard

# Create directories for server and client configurations
sudo mkdir -p /etc/wireguard/clients
sudo chmod 700 /etc/wireguard/clients


# Generate private and public keys
wg genkey | sudo tee /etc/wireguard/server_private.key
sudo cat /etc/wireguard/server_private.key | wg pubkey | sudo tee /etc/wireguard/server_public.key

echo "Public and Private Keys saved to /etc/wireguard/"


# Set proper permissions
sudo chmod 600 /etc/wireguard/server_private.key


# Automatically detect the main network interface (the one with the default route)
MAIN_INTERFACE=$(ip -o -4 route show to default | awk '{print $5}')
echo "Detected main network interface: $MAIN_INTERFACE"

# Create WireGuard server configuration
sudo bash -c "cat > /etc/wireguard/wg0.conf << EOF
[Interface]
PrivateKey = \$(cat /etc/wireguard/server_private.key)
Address = 10.0.0.1/24
DNS = 1.1.1.1, 8.8.8.8
ListenPort = 51820
SaveConfig = true
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o ${MAIN_INTERFACE} -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o ${MAIN_INTERFACE} -j MASQUERADE
EOF"



# Enable IP forwarding in the kernel settings
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf

# Allow WireGuard UDP port in the system firewall
# Check if UFW is active and configure safely
if sudo ufw status | grep -q "Status: active"; then
    echo "UFW is already enabled, adding WireGuard port"
    sudo ufw allow 51820/udp
else
    echo "Enabling UFW and adding WireGuard port"
    sudo ufw allow 51820/udp
    sudo ufw allow ssh # For SSH access
    sudo ufw --force enable  # automatically answer yes to enable
fi

# Reload Kernel settings without rebooting
sudo sysctl -p

# Start WireGuard and enable at boot
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0


echo "WireGuard server installation complete!"
echo "Public key saved to /etc/wireguard/server_public.key"
echo "Server public key: $(cat /etc/wireguard/server_public.key)"
echo "Using network interface: $MAIN_INTERFACE"