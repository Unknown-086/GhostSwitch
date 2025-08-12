import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
import os
import re
import requests
import json


class GhostSwitchVPN:
    def __init__(self, master):
        # Creating the main window
        self.master = master
        master.title("GhostSwitch")

        # Set ttkbootstrap style (superhero theme looks good for a VPN app)
        self.style = Style(theme="superhero")

        self.API_BASE_URL = "http://51.112.111.180:5000/api"

        # Set application icon
        # Make sure to create an 'assets' folder with your icon
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'ghostswitch_icon.ico')
        if os.path.exists(icon_path):
            master.iconbitmap(icon_path)


        # Configure window size
        master.geometry("450x500")
        master.minsize(450, 550)
        master.maxsize(450, 550)

        # Variables for login/signup
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        
        # Create frames for different screens
        self.login_frame = tb.Frame(master)
        self.signup_frame = tb.Frame(master)
        
        # Create all screens
        self.create_login_screen()
        self.create_signup_screen()
        
        # Show login screen initially
        self.show_login_screen()
    
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
            foreground="#6c757d"  # Default gray color
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
            foreground="#6c757d"  # Default gray color
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
            foreground="#6c757d"  # Default gray color
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
    
    def validate_username_requirements(self, *args):
        """Validate username as user types and update UI accordingly"""
        username = self.username_var.get()
        
        # Check if username meets requirements
        if len(username) > 0:
            if len(username) >= 8:
                # Valid username - set text to green
                self.username_req.config(foreground="#28a745")  # Success green color
            else:
                # Invalid username - set text to red
                self.username_req.config(foreground="#dc3545")  # Danger red color
        else:
            # Empty username field - set to default gray
            self.username_req.config(foreground="#6c757d")        

        
    def validate_password_requirements(self, *args):
        """Validate password as user types and update UI accordingly"""
        password = self.password_var.get()
        
        # Check if password meets requirements
        if len(password) > 0:
            if self.is_password_valid(password):
                # Valid password - set text to green
                self.password_req.config(foreground="#28a745")  # Success green color
            else:
                # Invalid password - set text to red
                self.password_req.config(foreground="#dc3545")  # Danger red color
        else:
            self.password_req.config(foreground="#6c757d")


    def validate_confirm_password(self, *args):
        """Validate confirm password matches the original password"""
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()
        
        # Only validate if both fields have content
        if len(confirm_password) > 0:
            if password == confirm_password:
                # Passwords match - set text to green
                self.confirm_password_req.config(foreground="#28a745")  # Success green color
            else:
                # Passwords don't match - set text to red
                self.confirm_password_req.config(foreground="#dc3545")  # Danger red color
        else:
            # Empty confirm password field - set to default gray
            self.confirm_password_req.config(foreground="#6c757d")  # Default gray color
    

    def is_password_valid(self, password):
        """Check if password meets all requirements."""
        if len(password) == 0:  # Empty password field (initial state)
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
        self.login_frame.pack(fill="both", expand=True)
        # Add field clearing
        self.username_var.set("")
        self.password_var.set("")
        self.confirm_password_var.set("")
        # Clear status messages
        self.login_status.set("")
        
    def show_signup_screen(self):
        self.login_frame.pack_forget()
        self.signup_frame.pack(fill="both", expand=True)
        # Add field clearing
        self.username_var.set("")
        self.password_var.set("")
        self.confirm_password_var.set("")
        # Clear status messages
        self.signup_status.set("")
    
    def signup(self):
        username = self.username_var.get()
        password = self.password_var.get()
        confirm = self.confirm_password_var.get()
        
        if not username or not password or not confirm:
            self.signup_status.set("Please fill all fields")
            return
        
        # Check username length
        if len(username) < 8:
            self.signup_status.set("Username must be at least 8 characters")
            return
        
        # Validate password requirements
        if not self.is_password_valid(password):
            self.signup_status.set("Password doesn't meet the requirements")
            return
        
        if password != confirm:
            self.signup_status.set("Passwords do not match")
            return
        
        # Make actual API call
        try:
            response = requests.post(f"{self.API_BASE_URL}/register", 
                                json={"username": username, "password": password},
                                timeout=10)
            
            if response.status_code == 201:
                self.signup_status.set("Account created successfully!")
                self.username_var.set("")
                self.password_var.set("")
                self.confirm_password_var.set("")
                # Switch to login screen after 2 seconds
                self.master.after(2000, self.show_login_screen)
            else:
                error_msg = response.json().get('message', 'Registration failed')
                self.signup_status.set(error_msg)
                
        except Exception as e:
            self.signup_status.set("Connection error. Please try again.")

    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            self.login_status.set("Please enter both username and password")
            return
        
        # Make actual API call
        try:
            response = requests.post(f"{self.API_BASE_URL}/login",
                                json={"username": username, "password": password},
                                timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()['user']
                self.login_status.set("Login successful!")
                # TODO: Switch to main VPN interface
                print(f"Logged in as: {user_data['username']}")
            else:
                error_msg = response.json().get('message', 'Login failed')
                self.login_status.set(error_msg)
                
        except Exception as e:
            self.login_status.set("Connection error. Please try again.")



if __name__ == "__main__":
    root = tk.Tk()
    app = GhostSwitchVPN(root)
    root.mainloop()