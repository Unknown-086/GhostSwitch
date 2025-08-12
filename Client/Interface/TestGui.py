import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
import os
import re
import requests
import json
import threading
import queue
import subprocess
import platform


class BackgroundWireGuardChecker:
    def __init__(self, callback_queue):
        self.callback_queue = callback_queue
        self.status = "checking"
        
    def start_check(self):
        """Start WireGuard check in background thread"""
        thread = threading.Thread(target=self.check_wireguard, daemon=True)
        thread.start()
    
    def check_wireguard(self):
        """Check WireGuard installation in background"""
        try:
            system = platform.system()
            
            if system == "Windows":
                # Check for WireGuard on Windows
                try:
                    result = subprocess.run(
                        ["where", "wg"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if result.returncode == 0:
                        status = "installed"
                    else:
                        status = "not_installed"
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    status = "not_installed"
                    
            elif system == "Linux":
                # Check for WireGuard on Linux
                try:
                    result = subprocess.run(
                        ["which", "wg"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if result.returncode == 0:
                        status = "installed"
                    else:
                        status = "not_installed"
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    status = "not_installed"
            else:
                status = "not_supported"
                
        except Exception as e:
            status = "error"
        
        # Send result back to main thread
        self.callback_queue.put({
            'action': 'wireguard_check',
            'status': status
        })


class GhostSwitchVPN:
    def __init__(self, master):
        # Creating the main window
        self.master = master
        master.title("GhostSwitch")

        # Set ttkbootstrap style (superhero theme looks good for a VPN app)
        self.style = Style(theme="superhero")

        self.API_BASE_URL = "http://51.112.111.180:5000/api"

        # Create a queue for thread communication
        self.api_queue = queue.Queue()

        # Initialize WireGuard checker
        self.wireguard_status = "checking"
        self.wireguard_checker = BackgroundWireGuardChecker(self.api_queue)

        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'ghostswitch_icon.ico')
        if os.path.exists(icon_path):
            master.iconbitmap(icon_path)

        # Configure window size - Made larger for VPN screen
        master.geometry("500x600")
        master.minsize(500, 600)
        master.maxsize(500, 600)

        # Variables for login/signup
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()

        # Current user info
        self.current_user = None
        self.current_user_id = None

        # Create frames for different screens
        self.login_frame = tb.Frame(master)
        self.signup_frame = tb.Frame(master)
        self.vpn_frame = tb.Frame(master) 
        
        # Create all screens
        self.create_login_screen()
        self.create_signup_screen()
        self.create_vpn_screen() 
        
        # Show login screen initially
        self.show_login_screen()
        
        # Start background processes
        self.check_api_responses()
        self.wireguard_checker.start_check()
    
    def check_api_responses(self):
        """Check for completed API responses without blocking UI"""
        try:
            while True:
                response_data = self.api_queue.get_nowait()
                self.handle_api_response(response_data)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.master.after(100, self.check_api_responses)

    def handle_api_response(self, response_data):
        """Handle API responses on the main thread"""
        action = response_data['action']
        
        if action == 'login':
            success = response_data['success']
            data = response_data['data']
            
            if success:
                self.current_user = data['username']
                self.current_user_id = data['id']
                self.login_status.set("Login successful!")
                # Switch to VPN screen
                self.master.after(1000, self.show_vpn_screen)
            else:
                self.login_status.set(data.get('message', 'Login failed'))
        
        elif action == 'signup':
            success = response_data['success']
            data = response_data['data']
            
            if success:
                self.signup_status.set("Account created successfully!")
                # Clear form fields
                self.username_var.set("")
                self.password_var.set("")
                self.confirm_password_var.set("")
                self.master.after(2000, self.show_login_screen)
            else:
                self.signup_status.set(data.get('message', 'Registration failed'))
        
        elif action == 'wireguard_check':
            self.wireguard_status = response_data['status']
            self.update_wireguard_status_display()

    def create_login_screen(self):
        # Logo/Title
        logo_frame = tb.Frame(self.login_frame)
        logo_frame.pack(fill="x", pady=30)
        
        title = tb.Label(logo_frame, text="GhostSwitch", font=("Helvetica", 24, "bold"))
        title.pack()
        
        subtitle = tb.Label(logo_frame, text="Secure. Private. Fast.")
        subtitle.pack(pady=5)
        
        # Username
        username_frame = tb.Frame(self.login_frame)
        username_frame.pack(fill="x", padx=50, pady=10)
        
        username_label = tb.Label(username_frame, text="Username")
        username_label.pack(side="top", anchor="w")
        
        self.username_entry = tb.Entry(username_frame, textvariable=self.username_var)
        self.username_entry.pack(side="top", fill="x", pady=5)
        
        # Password
        password_frame = tb.Frame(self.login_frame)
        password_frame.pack(fill="x", padx=50, pady=10)
        
        password_label = tb.Label(password_frame, text="Password")
        password_label.pack(side="top", anchor="w")
        
        self.password_entry = tb.Entry(password_frame, textvariable=self.password_var, show="*")
        self.password_entry.pack(side="top", fill="x", pady=5)
        
        # Login button
        button_frame = tb.Frame(self.login_frame)
        button_frame.pack(fill="x", padx=50, pady=20)
        
        login_button = tb.Button(
            button_frame, 
            text="Login",
            style="primary.TButton",
            command=self.login
        )
        login_button.pack(fill="x")
        
        # Sign up link
        signup_frame = tb.Frame(self.login_frame)
        signup_frame.pack(fill="x", pady=10)
        
        signup_text = tb.Label(signup_frame, text="Don't have an account?")
        signup_text.pack(side="left", padx=(50, 5))
        
        signup_link = tb.Label(
            signup_frame, 
            text="Sign up", 
            foreground="#3498db", 
            cursor="hand2"
        )
        signup_link.pack(side="left")
        signup_link.bind("<Button-1>", lambda e: self.show_signup_screen())
        
        # Status message
        self.login_status = tk.StringVar()
        status_label = tb.Label(self.login_frame, textvariable=self.login_status)
        status_label.pack(pady=10)
    
    def create_signup_screen(self):
        # Title
        title_frame = tb.Frame(self.signup_frame)
        title_frame.pack(fill="x", pady=30)
        
        title = tb.Label(title_frame, text="Create Account", font=("Helvetica", 24, "bold"))
        title.pack()
        
        # Username
        username_frame = tb.Frame(self.signup_frame)
        username_frame.pack(fill="x", padx=50, pady=10)
        
        username_label = tb.Label(username_frame, text="Username")
        username_label.pack(side="top", anchor="w")
        
        self.username_req = tb.Label(
            username_frame, 
            text="Minimum 8 characters required",
            font=("Helvetica", 8),
            foreground="#6c757d"
        )
        self.username_req.pack(side="top", anchor="w")
        
        self.signup_username_entry = tb.Entry(username_frame, textvariable=self.username_var)
        self.signup_username_entry.pack(side="top", fill="x", pady=5)
        
        # Add username validation on keyup
        self.username_var.trace_add("write", self.validate_username_requirements)
        
        # Password with requirements
        password_frame = tb.Frame(self.signup_frame)
        password_frame.pack(fill="x", padx=50, pady=10)
        
        password_label = tb.Label(password_frame, text="Password")
        password_label.pack(side="top", anchor="w")
        
        self.password_req = tb.Label(
            password_frame, 
            text="Must contain: 8+ chars, number, letter, special char",
            font=("Helvetica", 8),
            foreground="#6c757d"
        )
        self.password_req.pack(side="top", anchor="w")
        
        self.signup_password_entry = tb.Entry(password_frame, textvariable=self.password_var, show="*")
        self.signup_password_entry.pack(side="top", fill="x", pady=5)
        
        # Add password validation on keyup
        self.password_var.trace_add("write", self.validate_password_requirements)
        
        # Confirm Password
        confirm_frame = tb.Frame(self.signup_frame)
        confirm_frame.pack(fill="x", padx=50, pady=10)
        
        confirm_label = tb.Label(confirm_frame, text="Confirm Password")
        confirm_label.pack(side="top", anchor="w")
        
        self.confirm_password_req = tb.Label(
            confirm_frame, 
            text="Passwords must match",
            font=("Helvetica", 8),
            foreground="#6c757d"
        )
        self.confirm_password_req.pack(side="top", anchor="w")
        
        self.confirm_password_entry = tb.Entry(confirm_frame, textvariable=self.confirm_password_var, show="*")
        self.confirm_password_entry.pack(side="top", fill="x", pady=5)
        
        # Add confirm password validation on keyup
        self.confirm_password_var.trace_add("write", self.validate_confirm_password)
        
        # Buttons
        button_frame = tb.Frame(self.signup_frame)
        button_frame.pack(fill="x", padx=50, pady=20)
        
        create_button = tb.Button(
            button_frame, 
            text="Create Account", 
            style="primary.TButton",
            command=self.signup
        )
        create_button.pack(fill="x")
        
        # Back to login link
        back_frame = tb.Frame(self.signup_frame)
        back_frame.pack(fill="x", pady=10)
        
        back_text = tb.Label(back_frame, text="Already have an account?")
        back_text.pack(side="left", padx=(50, 5))
        
        back_link = tb.Label(
            back_frame, 
            text="Login", 
            foreground="#3498db", 
            cursor="hand2"
        )
        back_link.pack(side="left")
        back_link.bind("<Button-1>", lambda e: self.show_login_screen())
        
        # Status message
        self.signup_status = tk.StringVar()
        status_label = tb.Label(self.signup_frame, textvariable=self.signup_status)
        status_label.pack(pady=10)
    
    def create_vpn_screen(self):
        """Create the main VPN dashboard with enhanced visuals"""
        
        # Main container with padding
        main_container = tb.Frame(self.vpn_frame)
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header section - REMOVED style="info.TFrame" to remove light blue background
        header_frame = tb.Frame(main_container, padding=10)
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Title with icon-like styling
        title_container = tb.Frame(header_frame)
        title_container.pack(side="left")
        
        # # App icon/logo (using emoji as placeholder)
        # icon_label = tb.Label(title_container, text="🛡️", font=("Helvetica", 20))
        # icon_label.pack(side="left", padx=(0, 8))
        
        title_text = tb.Frame(title_container)
        title_text.pack(side="left")
        
        app_title = tb.Label(title_text, text="GhostSwitch", 
                            font=("Helvetica", 16, "bold"))
        app_title.pack(anchor="w")
        
        subtitle = tb.Label(title_text, text="Secure VPN Connection", 
                        font=("Helvetica", 9), foreground="#6c757d")
        subtitle.pack(anchor="w")
        
        # User info section with better styling
        user_container = tb.Frame(header_frame)
        user_container.pack(side="right")
        
        # User avatar (using emoji)
        user_avatar = tb.Label(user_container, text="👤", font=("Helvetica", 14))
        user_avatar.pack(side="right", padx=(8, 3))
        
        user_info_frame = tb.Frame(user_container)
        user_info_frame.pack(side="right")
        
        self.user_label = tb.Label(user_info_frame, text="", font=("Helvetica", 9, "bold"))
        self.user_label.pack(anchor="e")
        
        logout_btn = tb.Button(user_info_frame, text="Logout", 
                            style="outline.TButton", 
                            command=self.logout,
                            width=6)
        logout_btn.pack(anchor="e", pady=(2, 0))
        
        # Connection Status Card with enhanced design
        status_card = tb.LabelFrame(main_container, text="🔌 Connection Status", 
                                padding=15, style="success.TLabelframe")
        status_card.pack(fill="x", pady=(0, 10))
        
        # Status indicator with visual elements
        status_container = tb.Frame(status_card)
        status_container.pack(fill="x")
        
        # Large status indicator
        indicator_frame = tb.Frame(status_container)
        indicator_frame.pack(side="left", padx=(0, 15))
        
        # Fixed canvas background color issue
        self.status_circle = tk.Canvas(indicator_frame, width=50, height=50, 
                                    highlightthickness=0, bg="#2c3e50")
        self.status_circle.pack()
        
        # Initial disconnected state
        self.status_circle.create_oval(3, 3, 47, 47, fill="#dc3545", outline="#dc3545", width=2)
        self.status_circle.create_text(25, 25, text="❌", font=("Helvetica", 14), fill="white")
        
        # Status text and details
        status_text_frame = tb.Frame(status_container)
        status_text_frame.pack(side="left", fill="x", expand=True)
        
        self.connection_status_label = tb.Label(status_text_frame, text="Disconnected", 
                                            font=("Helvetica", 14, "bold"), 
                                            foreground="#dc3545")
        self.connection_status_label.pack(anchor="w")
        
        self.connection_detail_label = tb.Label(status_text_frame, 
                                            text="Not connected to any server", 
                                            font=("Helvetica", 9),
                                            foreground="#6c757d")
        self.connection_detail_label.pack(anchor="w", pady=(2, 0))
        
        # IP Address display
        ip_container = tb.Frame(status_container)
        ip_container.pack(side="right")
        
        ip_icon = tb.Label(ip_container, text="🌐", font=("Helvetica", 12))
        ip_icon.pack()
        
        self.ip_label = tb.Label(ip_container, text="IP: Hidden", 
                                font=("Helvetica", 9, "bold"))
        self.ip_label.pack()
        
        # System Status Card with enhanced design
        system_card = tb.LabelFrame(main_container, text="⚙️ System Status", 
                                padding=15, style="info.TLabelframe")
        system_card.pack(fill="x", pady=(0, 10))
        
        # WireGuard status with icon and progress-like display
        wg_container = tb.Frame(system_card)
        wg_container.pack(fill="x")
        
        wg_icon = tb.Label(wg_container, text="🔧", font=("Helvetica", 12))
        wg_icon.pack(side="left", padx=(0, 8))
        
        wg_info_frame = tb.Frame(wg_container)
        wg_info_frame.pack(side="left", fill="x", expand=True)
        
        wg_title = tb.Label(wg_info_frame, text="WireGuard Client", 
                        font=("Helvetica", 11, "bold"))
        wg_title.pack(anchor="w")
        
        self.wireguard_status_label = tb.Label(wg_info_frame, text="Checking installation...", 
                                            font=("Helvetica", 9))
        self.wireguard_status_label.pack(anchor="w")
        
        # Progress bar for checking status
        self.wg_progress = tb.Progressbar(wg_container, mode='indeterminate', length=80)
        self.wg_progress.pack(side="right")
        self.wg_progress.start()  # Start animation while checking
        
        # VPN Controls Section with better layout
        controls_card = tb.LabelFrame(main_container, text="🚀 VPN Controls", 
                                    padding=15, style="primary.TLabelframe")
        controls_card.pack(fill="x", pady=(0, 10))
        
        # Server selection with enhanced design
        server_container = tb.Frame(controls_card)
        server_container.pack(fill="x", pady=(0, 12))
        
        server_label_frame = tb.Frame(server_container)
        server_label_frame.pack(fill="x", pady=(0, 5))
        
        server_icon = tb.Label(server_label_frame, text="🌍", font=("Helvetica", 11))
        server_icon.pack(side="left", padx=(0, 3))
        
        server_label = tb.Label(server_label_frame, text="Select Server Location:", 
                            font=("Helvetica", 10, "bold"))
        server_label.pack(side="left")
        
        # Server dropdown with better styling
        self.server_var = tk.StringVar()
        self.server_dropdown = tb.Combobox(server_container, 
                                        textvariable=self.server_var,
                                        state="readonly", 
                                        font=("Helvetica", 9),
                                        width=45)
        self.server_dropdown.pack(fill="x")
        
        # Dummy server data with flags
        dummy_servers = [
            "🇺🇸 United States - New York (Ultra Fast)",
            "🇺🇸 United States - Los Angeles (Fast)", 
            "🇬🇧 United Kingdom - London (Fast)",
            "🇩🇪 Germany - Frankfurt (Medium)",
            "🇸🇬 Singapore - Singapore (Fast)",
            "🇯🇵 Japan - Tokyo (Medium)",
            "🇨🇦 Canada - Toronto (Fast)"
        ]
        self.server_dropdown['values'] = dummy_servers
        if dummy_servers:
            self.server_dropdown.set(dummy_servers[0])
        
        # Connection buttons - REMOVED Quick Connect button
        button_container = tb.Frame(controls_card)
        button_container.pack(fill="x", pady=(8, 0))
        
        # Main connect button - Made wider since we removed quick connect
        self.connect_btn = tb.Button(button_container, 
                                    text="🔒 Connect VPN", 
                                    style="success.TButton",
                                    command=self.toggle_connection,
                                    width=25)  # Made wider
        self.connect_btn.pack(side="left", padx=(0, 10))
        
        # Refresh servers button
        refresh_btn = tb.Button(button_container, 
                            text="🔄 Refresh", 
                            style="outline.TButton",
                            command=self.refresh_servers,
                            width=10)
        refresh_btn.pack(side="right")
        
        # Statistics section (initially hidden)
        self.stats_card = tb.LabelFrame(main_container, text="📊 Connection Statistics", 
                                    padding=15, style="secondary.TLabelframe")
        
        # Create stats content
        stats_container = tb.Frame(self.stats_card)
        stats_container.pack(fill="x")
        
        # Stats grid with icons
        stats_grid = tb.Frame(stats_container)
        stats_grid.pack(fill="x")
        
        # Duration
        duration_frame = tb.Frame(stats_grid)
        duration_frame.pack(fill="x", pady=1)
        tb.Label(duration_frame, text="⏱️", font=("Helvetica", 10)).pack(side="left", padx=(0, 3))
        tb.Label(duration_frame, text="Duration:", font=("Helvetica", 9)).pack(side="left")
        self.duration_label = tb.Label(duration_frame, text="00:00:00", 
                                    font=("Helvetica", 9, "bold"), foreground="#28a745")
        self.duration_label.pack(side="right")
        
        # Data sent
        sent_frame = tb.Frame(stats_grid)
        sent_frame.pack(fill="x", pady=1)
        tb.Label(sent_frame, text="📤", font=("Helvetica", 10)).pack(side="left", padx=(0, 3))
        tb.Label(sent_frame, text="Data Sent:", font=("Helvetica", 9)).pack(side="left")
        self.data_sent_label = tb.Label(sent_frame, text="0 MB", 
                                    font=("Helvetica", 9, "bold"), foreground="#007bff")
        self.data_sent_label.pack(side="right")
        
        # Data received
        received_frame = tb.Frame(stats_grid)
        received_frame.pack(fill="x", pady=1)
        tb.Label(received_frame, text="📥", font=("Helvetica", 10)).pack(side="left", padx=(0, 3))
        tb.Label(received_frame, text="Data Received:", font=("Helvetica", 9)).pack(side="left")
        self.data_received_label = tb.Label(received_frame, text="0 MB", 
                                        font=("Helvetica", 9, "bold"), foreground="#28a745")
        self.data_received_label.pack(side="right")
        
        # Speed
        speed_frame = tb.Frame(stats_grid)
        speed_frame.pack(fill="x", pady=1)
        tb.Label(speed_frame, text="🚀", font=("Helvetica", 10)).pack(side="left", padx=(0, 3))
        tb.Label(speed_frame, text="Speed:", font=("Helvetica", 9)).pack(side="left")
        self.speed_label = tb.Label(speed_frame, text="0 Mbps", 
                                font=("Helvetica", 9, "bold"), foreground="#ffc107")
        self.speed_label.pack(side="right")

    def validate_username_requirements(self, *args):
        """Validate username as user types and update UI accordingly"""
        username = self.username_var.get()
        
        if len(username) > 0:
            if len(username) >= 8:
                self.username_req.config(foreground="#28a745")  # Green
            else:
                self.username_req.config(foreground="#dc3545")  # Red
        else:
            self.username_req.config(foreground="#6c757d")  # Gray

    def validate_password_requirements(self, *args):
        """Validate password as user types and update UI accordingly"""
        password = self.password_var.get()
        
        if len(password) > 0:
            if self.is_password_valid(password):
                self.password_req.config(foreground="#28a745")  # Green
            else:
                self.password_req.config(foreground="#dc3545")  # Red
        else:
            self.password_req.config(foreground="#6c757d")  # Gray

        # Also validate confirm password when password changes
        self.validate_confirm_password()

    def validate_confirm_password(self, *args):
        """Validate confirm password matches the original password"""
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()
        
        if len(confirm_password) > 0:
            if password == confirm_password:
                self.confirm_password_req.config(foreground="#28a745")  # Green
            else:
                self.confirm_password_req.config(foreground="#dc3545")  # Red
        else:
            self.confirm_password_req.config(foreground="#6c757d")  # Gray

    def is_password_valid(self, password):
        """Check if password meets all requirements."""
        if len(password) == 0:
            return False
            
        # Minimum length check (8 characters)
        if len(password) < 8:
            return False
        
        # Check for at least one letter
        if not re.search(r'[a-zA-Z]', password):
            return False
            
        # Check for at least one digit
        if not re.search(r'\d', password):
            return False
            
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
            
        return True
        
    # Navigation functions
    def show_login_screen(self):
        self.signup_frame.pack_forget()
        self.vpn_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        
        # Clear fields and status
        self.username_var.set("")
        self.password_var.set("")
        self.confirm_password_var.set("")
        self.login_status.set("")
        
    def show_signup_screen(self):
        self.login_frame.pack_forget()
        self.vpn_frame.pack_forget()
        self.signup_frame.pack(fill="both", expand=True)
        
        # Clear fields and status
        self.username_var.set("")
        self.password_var.set("")
        self.confirm_password_var.set("")
        self.signup_status.set("")

    def show_vpn_screen(self):
        """Show the VPN dashboard"""
        self.login_frame.pack_forget()
        self.signup_frame.pack_forget()
        self.vpn_frame.pack(fill="both", expand=True)
        
        # Update user label
        if self.current_user:
            self.user_label.config(text=f"Welcome, {self.current_user}")

    def logout(self):
        """Logout and return to login screen"""
        self.current_user = None
        self.current_user_id = None
        self.show_login_screen()

    def signup(self):
        username = self.username_var.get()
        password = self.password_var.get()
        confirm = self.confirm_password_var.get()
        
        if not username or not password or not confirm:
            self.signup_status.set("Please fill all fields")
            return
        
        if len(username) < 8:
            self.signup_status.set("Username must be at least 8 characters")
            return
        
        if not self.is_password_valid(password):
            self.signup_status.set("Password doesn't meet the requirements")
            return
        
        if password != confirm:
            self.signup_status.set("Passwords do not match")
            return
        
        # Show loading state
        self.signup_status.set("Creating account...")
        
        # Start API call in background thread (now non-blocking)
        thread = threading.Thread(
            target=self.api_signup_thread,
            args=(username, password),
            daemon=True
        )
        thread.start()

    def api_signup_thread(self, username, password):
        """Handle signup API call in background thread"""
        try:
            response = requests.post(f"{self.API_BASE_URL}/register", 
                                json={"username": username, "password": password},
                                timeout=10)
            
            if response.status_code == 201:
                self.api_queue.put({
                    'action': 'signup',
                    'success': True,
                    'data': {'message': 'Account created successfully!'}
                })
            else:
                error_msg = response.json().get('message', 'Registration failed')
                self.api_queue.put({
                    'action': 'signup',
                    'success': False,
                    'data': {'message': error_msg}
                })
                
        except requests.exceptions.RequestException as e:
            self.api_queue.put({
                'action': 'signup',
                'success': False,
                'data': {'message': 'Connection error. Please try again.'}
            })

    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            self.login_status.set("Please enter both username and password")
            return
        
        # Show loading state
        self.login_status.set("Logging in...")
        
        # Start API call in background thread
        thread = threading.Thread(
            target=self.api_login_thread,
            args=(username, password),
            daemon=True
        )
        thread.start()

    def api_login_thread(self, username, password):
        """Handle login API call in background thread"""
        try:
            response = requests.post(f"{self.API_BASE_URL}/login",
                                json={"username": username, "password": password},
                                timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()['user']
                self.api_queue.put({
                    'action': 'login',
                    'success': True,
                    'data': user_data
                })
            else:
                error_msg = response.json().get('message', 'Login failed')
                self.api_queue.put({
                    'action': 'login',
                    'success': False,
                    'data': {'message': error_msg}
                })
                
        except requests.exceptions.RequestException as e:
            self.api_queue.put({
                'action': 'login',
                'success': False,
                'data': {'message': 'Connection error. Please try again.'}
            })

    def toggle_connection(self):
        """Toggle VPN connection with visual feedback"""
        # Placeholder for now - will implement actual VPN logic later
        current_text = self.connect_btn.cget('text')
        
        if "Connect" in current_text:
            # Simulate connecting
            self.connect_btn.config(text="🔓 Disconnect VPN", style="danger.TButton")
            self.update_connection_visual_status("connected")
            self.show_stats()
        else:
            # Simulate disconnecting
            self.connect_btn.config(text="🔒 Connect VPN", style="success.TButton")
            self.update_connection_visual_status("disconnected")
            self.hide_stats()


    def refresh_servers(self):
        """Refresh server list"""
        # Placeholder - could add API call to refresh servers
        pass

    def update_connection_visual_status(self, status):
        """Update visual connection status"""
        if status == "connected":
            # Update circle to green with checkmark
            self.status_circle.delete("all")
            self.status_circle.create_oval(3, 3, 47, 47, fill="#28a745", outline="#28a745", width=2)
            self.status_circle.create_text(25, 25, text="✓", font=("Helvetica", 16, "bold"), fill="white")
            
            # Update labels
            self.connection_status_label.config(text="Connected", foreground="#28a745")
            selected_server = self.server_var.get()
            if selected_server:
                server_name = selected_server.split(" - ")[1].split(" (")[0]
                self.connection_detail_label.config(text=f"Connected to {server_name}")
            
            self.ip_label.config(text="IP: 192.168.1.100")  # Placeholder IP
            
        else:
            # Update circle to red with X
            self.status_circle.delete("all")
            self.status_circle.create_oval(3, 3, 47, 47, fill="#dc3545", outline="#dc3545", width=2)
            self.status_circle.create_text(25, 25, text="❌", font=("Helvetica", 14), fill="white")
            
            # Update labels
            self.connection_status_label.config(text="Disconnected", foreground="#dc3545")
            self.connection_detail_label.config(text="Not connected to any server")
            self.ip_label.config(text="IP: Hidden")

    def show_stats(self):
        """Show connection statistics"""
        self.stats_card.pack(fill="x", pady=(0, 10))
        # Start updating stats (placeholder)
        self.update_stats()

    def hide_stats(self):
        """Hide connection statistics"""
        self.stats_card.pack_forget()

    def update_stats(self):
        """Update connection statistics (placeholder)"""
        # This would be replaced with real stats later
        import random
        if hasattr(self, 'stats_card') and self.stats_card.winfo_viewable():
            # Simulate some stats
            self.data_sent_label.config(text=f"{random.randint(10, 500)} MB")
            self.data_received_label.config(text=f"{random.randint(50, 1000)} MB")
            self.speed_label.config(text=f"{random.randint(20, 100)} Mbps")
            
            # Schedule next update
            self.master.after(2000, self.update_stats)

    def update_wireguard_status_display(self):
        """Update WireGuard status in UI with enhanced visuals"""
        if hasattr(self, 'wireguard_status_label'):
            # Stop progress bar animation
            if hasattr(self, 'wg_progress'):
                self.wg_progress.stop()
                self.wg_progress.pack_forget()
            
            if self.wireguard_status == "installed":
                self.wireguard_status_label.config(
                    text="✅ Installed and ready", 
                    foreground="#28a745"
                )
            elif self.wireguard_status == "not_installed":
                self.wireguard_status_label.config(
                    text="❌ Not installed - Download required", 
                    foreground="#dc3545"
                )
            elif self.wireguard_status == "checking":
                self.wireguard_status_label.config(
                    text="🔄 Checking installation...", 
                    foreground="#6c757d"
                )
            else:
                self.wireguard_status_label.config(
                    text="⚠️ Error checking installation", 
                    foreground="#ffc107"
                )


if __name__ == "__main__":
    root = tk.Tk()
    app = GhostSwitchVPN(root)
    root.mainloop()