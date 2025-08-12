

sudo apt update
sudo apt install mysql-client -y

# Your Endpoint and username
mysql -h test-database.cnccs0uoe80h.me-central-1.rds.amazonaws.com -u root -p


# for installing Python libraries in ubuntu
sudo apt install python3-pip -y

# Install required Python packages
sudo apt install python3 python3-pip python3-venv python3-openssl libssl-dev -y

# Create a virtual environment
python3 -m venv myenv
source myenv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the latest MySQL connector
pip install mysql-connector-python



