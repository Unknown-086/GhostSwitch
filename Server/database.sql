CREATE DATABASE ghostswitch;
USE ghostswitch;


CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

CREATE TABLE vpn_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    server_id INT NOT NULL,
    client_public_key VARCHAR(255) NOT NULL,
    client_private_key VARCHAR(255) NOT NULL,
    assigned_ip VARCHAR(15) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    location VARCHAR(50) NOT NULL,
    public_ip VARCHAR(15) NOT NULL,
    endpoint VARCHAR(21) NOT NULL,
    public_key VARCHAR(255) NOT NULL,
    status ENUM('active', 'maintenance', 'offline') DEFAULT 'active'
);



-- One Line SQL Script to create the database and tables
CREATE TABLE users ( id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL, salt VARCHAR(50) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP NULL ); CREATE TABLE vpn_configs ( id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, server_id INT NOT NULL, client_public_key VARCHAR(255) NOT NULL,    client_private_key VARCHAR(255) NOT NULL, assigned_ip VARCHAR(15) NOT NULL,    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id) ); CREATE TABLE servers ( id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50) NOT NULL, location VARCHAR(50) NOT NULL, public_ip VARCHAR(15) NOT NULL, endpoint VARCHAR(21) NOT NULL, public_key VARCHAR(255) NOT NULL, status ENUM('active', 'maintenance', 'offline') DEFAULT 'active' );




-- Add is_active column to vpn_configs if it doesn't exist
ALTER TABLE vpn_configs ADD COLUMN is_active BOOLEAN DEFAULT TRUE;

-- Create connections log table (optional)
CREATE TABLE connection_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action ENUM('connect', 'disconnect') NOT NULL,
    server_endpoint VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);


-- Add is_active column to vpn_configs if it doesn't exist
ALTER TABLE vpn_configs ADD COLUMN is_active BOOLEAN DEFAULT TRUE; CREATE TABLE connection_logs ( id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, action ENUM('connect', 'disconnect') NOT NULL, server_endpoint VARCHAR(100), timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id) );



-- Add your real server to the database
INSERT INTO servers (name, location, public_ip, endpoint, public_key, status) VALUES ('Dubai Server', 'Dubai, UAE', '51.112.111.180', '51.112.111.180:51820', '198Q3PykQ81WMNpy3FuO978z+y4iTk9ssNzi9KzCF3o=', 'active');