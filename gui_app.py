"""
Live Face Verification System - GUI Application (v2)
Modern GUI using CustomTkinter with improved validations
"""
import os
import sys
import threading
import time
import shutil
import re
from datetime import datetime
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox
import cv2

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.camera import Camera
from modules.face_detector import FaceDetector
from modules.embeddings import EmbeddingGenerator  
from modules.verifier import Verifier
from modules.liveness import LivenessDetector
from database.db_manager import DatabaseManager
from config import ENROLLED_IMAGES_DIR, LIVENESS_ENABLED

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VerificationPopup(ctk.CTkToplevel):
    """Professional verification result popup"""
    
    def __init__(self, parent, verified, user_name=None, confidence=0, on_close=None):
        super().__init__(parent)
        
        self.on_close_callback = on_close
        
        # Window setup - BIGGER SIZE
        self.title("")
        self.geometry("420x450")
        self.resizable(False, False)
        
        # Center on screen (not parent to avoid blocking)
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - 420) // 2
        y = (screen_h - 450) // 2
        self.geometry(f"+{x}+{y}")
        
        # Remove title bar and make topmost
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Main frame with rounded corners effect
        if verified:
            main_color = "#1a472a"  # Dark green
            accent_color = "#2d6a4f"
            icon = "✅"
            title = "ACCESS GRANTED"
            message = f"Welcome back, {user_name}!"
        else:
            main_color = "#4a1a1a"  # Dark red
            accent_color = "#6a2d2d"
            icon = "❌"
            title = "ACCESS DENIED"
            message = "Face not recognized"
        
        main_frame = ctk.CTkFrame(self, fg_color=main_color, corner_radius=20)
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame, text="✕", width=35, height=35,
            fg_color="transparent", hover_color=accent_color,
            font=ctk.CTkFont(size=18),
            command=self._close
        )
        close_btn.place(relx=0.95, rely=0.02, anchor="ne")
        
        # Icon
        ctk.CTkLabel(
            main_frame, text=icon,
            font=ctk.CTkFont(size=70)
        ).pack(pady=(40, 15))
        
        # Title
        ctk.CTkLabel(
            main_frame, text=title,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="white"
        ).pack(pady=10)
        
        # Message
        ctk.CTkLabel(
            main_frame, text=message,
            font=ctk.CTkFont(size=18),
            text_color="#cccccc"
        ).pack(pady=10)
        
        # Confidence bar
        conf_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        conf_frame.pack(pady=15, fill="x", padx=50)
        
        ctk.CTkLabel(
            conf_frame, text=f"Confidence: {confidence:.1f}%",
            font=ctk.CTkFont(size=16)
        ).pack()
        
        conf_bar = ctk.CTkProgressBar(conf_frame, width=250, height=15)
        conf_bar.pack(pady=8)
        conf_bar.set(confidence / 100)
        
        # Timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ctk.CTkLabel(
            main_frame, text=f"🕐 {timestamp}",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        ).pack(pady=8)
        
        # OK button - BIGGER
        ctk.CTkButton(
            main_frame, text="OK",
            width=150, height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=accent_color,
            hover_color=main_color,
            command=self._close
        ).pack(pady=20)
        
        # Auto close after 5 seconds
        self.after(5000, self._close)
        
        # Focus
        self.focus_force()
    
    def _close(self):
        """Close popup and call callback"""
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()


class SuccessToast(ctk.CTkToplevel):
    """Small toast notification for quick feedback"""
    
    def __init__(self, parent, message, icon="✓", duration=2000):
        super().__init__(parent)
        
        self.title("")
        self.geometry("300x60")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Position at bottom-right of parent
        self.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() - 320
        y = parent.winfo_y() + parent.winfo_height() - 100
        self.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(self, fg_color="#2d6a4f", corner_radius=10)
        frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            frame, text=f"{icon} {message}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(expand=True)
        
        self.after(duration, self.destroy)


class FaceVerificationApp(ctk.CTk):
    """Main GUI Application with improved validations"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Face Verification System")
        self.geometry("1000x700")
        self.minsize(900, 600)
        
        # Show loading screen
        self._show_loading("Initializing system components...")
        
        # Initialize components in thread
        self.after(100, self._init_components)
    
    def _show_loading(self, message):
        """Show loading overlay"""
        self.loading_frame = ctk.CTkFrame(self)
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        ctk.CTkLabel(
            self.loading_frame,
            text="🔐 Face Verification System",
            font=ctk.CTkFont(size=32, weight="bold")
        ).pack(pady=(200, 20))
        
        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text=message,
            font=ctk.CTkFont(size=16)
        )
        self.loading_label.pack(pady=20)
        
        self.loading_progress = ctk.CTkProgressBar(self.loading_frame, width=300)
        self.loading_progress.pack(pady=20)
        self.loading_progress.configure(mode="indeterminate")
        self.loading_progress.start()
    
    def _hide_loading(self):
        """Hide loading overlay"""
        if hasattr(self, 'loading_frame'):
            self.loading_progress.stop()
            self.loading_frame.destroy()
    
    def _init_components(self):
        """Initialize system components"""
        try:
            self.loading_label.configure(text="Loading camera module...")
            self.update()
            self.camera = Camera()
            
            self.loading_label.configure(text="Loading face detector...")
            self.update()
            self.detector = FaceDetector()
            
            self.loading_label.configure(text="Loading embedding generator...")
            self.update()
            self.embedding_generator = EmbeddingGenerator()
            
            self.loading_label.configure(text="Loading verifier...")
            self.update()
            self.verifier = Verifier()
            self.liveness = LivenessDetector() if LIVENESS_ENABLED else None
            
            self.loading_label.configure(text="Connecting to database...")
            self.update()
            self.db = DatabaseManager()
            
            # State variables
            self.camera_running = False
            self.current_frame = None
            self.captured_faces = []
            self.captured_images = []
            self.is_processing = False
            
            # Hide loading and build UI
            self._hide_loading()
            self._create_layout()
            self._update_user_list()
            
            # Handle window close
            self.protocol("WM_DELETE_WINDOW", self._on_closing)
            
        except Exception as e:
            self._hide_loading()
            messagebox.showerror("Initialization Error", f"Failed to initialize system:\n\n{str(e)}")
            self.destroy()
    
    def _create_layout(self):
        """Create the main layout"""
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main_content()
    
    def _create_sidebar(self):
        """Create sidebar with navigation"""
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(7, weight=1)
        
        # Logo/Title
        ctk.CTkLabel(
            sidebar, text="🔐 Face ID",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            sidebar, text="● Ready",
            font=ctk.CTkFont(size=12),
            text_color="green"
        )
        self.status_label.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Navigation buttons
        ctk.CTkButton(
            sidebar, text="🏠 Home",
            command=self._show_home_panel,
            height=40, font=ctk.CTkFont(size=14)
        ).grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkButton(
            sidebar, text="📷 Enroll User",
            command=self._show_enroll_panel,
            height=40, font=ctk.CTkFont(size=14)
        ).grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkButton(
            sidebar, text="✓ Verify Face",
            command=self._show_verify_panel,
            height=40, font=ctk.CTkFont(size=14)
        ).grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkButton(
            sidebar, text="👥 Manage Users",
            command=self._show_users_panel,
            height=40, font=ctk.CTkFont(size=14)
        ).grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        
        # Stats frame
        stats_frame = ctk.CTkFrame(sidebar)
        stats_frame.grid(row=7, column=0, padx=20, pady=20, sticky="sew")
        
        stats = self.db.get_statistics()
        self.lbl_stats = ctk.CTkLabel(
            stats_frame,
            text=f"👥 Users: {stats['total_users']}\n📊 Embeddings: {stats['total_embeddings']}",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_stats.pack(padx=10, pady=10)
    
    def _create_main_content(self):
        """Create main content area"""
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        self._create_home_panel()
        self._create_enroll_panel()
        self._create_verify_panel()
        self._create_users_panel()
        
        self._show_home_panel()
    
    def _create_home_panel(self):
        """Create home panel"""
        self.home_panel = ctk.CTkFrame(self.content_frame)
        
        ctk.CTkLabel(
            self.home_panel,
            text="Welcome to Face Verification System",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(80, 20))
        
        ctk.CTkLabel(
            self.home_panel,
            text="Secure identity verification using facial recognition",
            font=ctk.CTkFont(size=16)
        ).pack(pady=10)
        
        # Quick actions
        actions = ctk.CTkFrame(self.home_panel)
        actions.pack(pady=50)
        
        ctk.CTkButton(
            actions, text="📷 Enroll New User",
            command=self._show_enroll_panel,
            width=200, height=50,
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=15)
        
        ctk.CTkButton(
            actions, text="✓ Start Verification",
            command=self._show_verify_panel,
            width=200, height=50,
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=15)
        
        # Instructions
        instructions = ctk.CTkFrame(self.home_panel)
        instructions.pack(pady=30, fill="x", padx=50)
        
        ctk.CTkLabel(
            instructions,
            text="📋 Quick Guide",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 10))
        
        guide_text = """
1️⃣ ENROLL: Add new users with face photos (webcam or upload)
2️⃣ VERIFY: Check identity against enrolled users
3️⃣ MANAGE: View, search, and delete users
        """
        ctk.CTkLabel(
            instructions,
            text=guide_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        ).pack(pady=(0, 15))
    
    def _create_enroll_panel(self):
        """Create enrollment panel with validations"""
        self.enroll_panel = ctk.CTkFrame(self.content_frame)
        self.enroll_panel.grid_columnconfigure(0, weight=1)
        self.enroll_panel.grid_columnconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(
            self.enroll_panel,
            text="👤 User Enrollment",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=20)
        
        # Left side - Form
        form_frame = ctk.CTkFrame(self.enroll_panel)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # User ID
        ctk.CTkLabel(form_frame, text="User ID:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.entry_user_id = ctk.CTkEntry(form_frame, width=250, placeholder_text="Leave empty for auto-generate")
        self.entry_user_id.pack(pady=5)
        self.user_id_error = ctk.CTkLabel(form_frame, text="", font=ctk.CTkFont(size=11), text_color="red")
        self.user_id_error.pack()
        
        # Name
        ctk.CTkLabel(form_frame, text="Full Name: *", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.entry_name = ctk.CTkEntry(form_frame, width=250, placeholder_text="Required - Enter full name")
        self.entry_name.pack(pady=5)
        self.name_error = ctk.CTkLabel(form_frame, text="", font=ctk.CTkFont(size=11), text_color="red")
        self.name_error.pack()
        
        # Bind validation
        self.entry_name.bind("<FocusOut>", self._validate_name)
        self.entry_user_id.bind("<FocusOut>", self._validate_user_id)
        
        # Buttons
        btn_frame = ctk.CTkFrame(form_frame)
        btn_frame.pack(pady=20)
        
        self.btn_webcam = ctk.CTkButton(
            btn_frame, text="📷 Start Camera",
            command=self._start_enroll_camera,
            width=200, height=40
        )
        self.btn_webcam.pack(padx=5)
        
        # Progress
        self.enroll_progress = ctk.CTkLabel(
            form_frame, text="📸 Captured: 0 images",
            font=ctk.CTkFont(size=14)
        )
        self.enroll_progress.pack(pady=15)
        
        self.enroll_progress_bar = ctk.CTkProgressBar(form_frame, width=200)
        self.enroll_progress_bar.pack(pady=5)
        self.enroll_progress_bar.set(0)
        
        # Save button
        self.btn_save = ctk.CTkButton(
            form_frame, text="💾 Save User",
            command=self._save_enrollment,
            width=200, height=40,
            fg_color="green", hover_color="darkgreen",
            state="disabled"
        )
        self.btn_save.pack(pady=15)
        
        # Reset button
        ctk.CTkButton(
            form_frame, text="🔄 Reset",
            command=self._reset_enrollment,
            width=100, fg_color="gray", hover_color="darkgray"
        ).pack(pady=5)
        
        # Right side - Preview
        preview_frame = ctk.CTkFrame(self.enroll_panel)
        preview_frame.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        
        self.enroll_camera_label = ctk.CTkLabel(
            preview_frame,
            text="📷 Camera Preview\n\nEnter name and click\n'Use Webcam' or 'Upload'\nto add face images",
            font=ctk.CTkFont(size=14)
        )
        self.enroll_camera_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Camera controls
        cam_btns = ctk.CTkFrame(preview_frame)
        cam_btns.pack(pady=10)
        
        self.btn_capture = ctk.CTkButton(
            cam_btns, text="📸 Capture",
            command=self._capture_frame,
            state="disabled", width=100
        )
        self.btn_capture.pack(side="left", padx=5)
        
        self.btn_stop_cam = ctk.CTkButton(
            cam_btns, text="⏹ Stop",
            command=self._stop_camera,
            state="disabled", width=80,
            fg_color="red", hover_color="darkred"
        )
        self.btn_stop_cam.pack(side="left", padx=5)
        
        # Enroll status
        self.enroll_status = ctk.CTkLabel(
            preview_frame, text="",
            font=ctk.CTkFont(size=12)
        )
        self.enroll_status.pack(pady=5)
    
    def _create_verify_panel(self):
        """Create verification panel"""
        self.verify_panel = ctk.CTkFrame(self.content_frame)
        self.verify_panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.verify_panel,
            text="✓ Face Verification",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)
        
        # Camera preview
        self.verify_camera_label = ctk.CTkLabel(
            self.verify_panel,
            text="📷 Camera Preview\n\nSelect verification method below",
            font=ctk.CTkFont(size=14)
        )
        self.verify_camera_label.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Result
        self.verify_result = ctk.CTkLabel(
            self.verify_panel, text="",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.verify_result.pack(pady=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.verify_panel)
        btn_frame.pack(pady=20)
        
        self.btn_live_verify = ctk.CTkButton(
            btn_frame, text="📷 Live Verification",
            command=self._start_verify_camera,
            width=180, height=40
        )
        self.btn_live_verify.pack(side="left", padx=10)
        
        # Image verification removed - Live only mode
        
        self.btn_stop_verify = ctk.CTkButton(
            btn_frame, text="⏹ Stop",
            command=self._stop_camera,
            width=80, height=40,
            fg_color="red", hover_color="darkred",
            state="disabled"
        )
        self.btn_stop_verify.pack(side="left", padx=10)
    
    def _create_users_panel(self):
        """Create user management panel"""
        self.users_panel = ctk.CTkFrame(self.content_frame)
        self.users_panel.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.users_panel,
            text="👥 Manage Users",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)
        
        # Search
        search_frame = ctk.CTkFrame(self.users_panel)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(search_frame, text="🔍 Search:").pack(side="left", padx=(10, 5))
        self.search_entry = ctk.CTkEntry(search_frame, width=200, placeholder_text="Search by name or ID")
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self._filter_users)
        
        ctk.CTkButton(
            search_frame, text="🔄 Refresh",
            command=self._update_user_list, width=100
        ).pack(side="right", padx=10)
        
        # Users list
        self.users_list_frame = ctk.CTkScrollableFrame(self.users_panel, height=400)
        self.users_list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.all_users_data = []
    
    # === Validation Methods ===
    
    def _validate_name(self, event=None):
        """Validate name field"""
        name = self.entry_name.get().strip()
        
        if not name:
            self.name_error.configure(text="⚠ Name is required")
            return False
        
        if len(name) < 2:
            self.name_error.configure(text="⚠ Name must be at least 2 characters")
            return False
        
        if len(name) > 100:
            self.name_error.configure(text="⚠ Name is too long (max 100 chars)")
            return False
        
        if not re.match(r'^[a-zA-Z\s\-\.]+$', name):
            self.name_error.configure(text="⚠ Name can only contain letters, spaces, hyphens")
            return False
        
        self.name_error.configure(text="")
        return True
    
    def _validate_user_id(self, event=None):
        """Validate user ID field"""
        user_id = self.entry_user_id.get().strip()
        
        if not user_id:
            self.user_id_error.configure(text="")  # Empty is OK (auto-generate)
            return True
        
        if len(user_id) < 3:
            self.user_id_error.configure(text="⚠ ID must be at least 3 characters")
            return False
        
        if not re.match(r'^[a-zA-Z0-9_\-]+$', user_id):
            self.user_id_error.configure(text="⚠ ID can only contain letters, numbers, underscore, hyphen")
            return False
        
        if self.db.user_exists(user_id):
            self.user_id_error.configure(text="⚠ This ID already exists!")
            return False
        
        self.user_id_error.configure(text="")
        return True
    
    def _set_status(self, message, color="green"):
        """Set status indicator"""
        self.status_label.configure(text=f"● {message}", text_color=color)
    
    def _set_processing(self, processing, message="Processing..."):
        """Set processing state"""
        self.is_processing = processing
        if processing:
            self._set_status(message, "orange")
        else:
            self._set_status("Ready", "green")
    
    # === Panel Navigation ===
    
    def _hide_all_panels(self):
        """Hide all panels"""
        for panel in [self.home_panel, self.enroll_panel, self.verify_panel, self.users_panel]:
            panel.grid_forget()
        self._stop_camera()
    
    def _show_home_panel(self):
        self._hide_all_panels()
        self.home_panel.grid(row=0, column=0, sticky="nsew")
        self._set_status("Ready", "green")
    
    def _show_enroll_panel(self):
        self._hide_all_panels()
        self._reset_enrollment()
        self.enroll_panel.grid(row=0, column=0, sticky="nsew")
        self._set_status("Enrollment", "blue")
    
    def _show_verify_panel(self):
        self._hide_all_panels()
        self.verify_result.configure(text="")
        self.verify_panel.grid(row=0, column=0, sticky="nsew")
        self._set_status("Verification", "blue")
    
    def _show_users_panel(self):
        self._hide_all_panels()
        self._update_user_list()
        self.users_panel.grid(row=0, column=0, sticky="nsew")
        self._set_status("User Management", "blue")
    
    # === Enrollment Methods ===
    
    def _reset_enrollment(self):
        """Reset enrollment state"""
        self.captured_faces = []
        self.captured_images = []
        self.entry_user_id.delete(0, "end")
        self.entry_name.delete(0, "end")
        self.name_error.configure(text="")
        self.user_id_error.configure(text="")
        self.enroll_progress.configure(text="📸 Captured: 0 images")
        self.enroll_progress_bar.set(0)
        self.btn_save.configure(state="disabled")
        self.enroll_status.configure(text="")
        self.enroll_camera_label.configure(
            text="📷 Camera Preview\n\nEnter name and click\n'Use Webcam' or 'Upload'\nto add face images",
            image=None
        )
    
    def _start_enroll_camera(self):
        """Start camera for enrollment"""
        if not self._validate_name():
            messagebox.showwarning("Validation Error", "Please enter a valid name first!")
            self.entry_name.focus()
            return
        
        if not self._validate_user_id():
            if self.entry_user_id.get().strip():  # Only warn if ID was entered
                messagebox.showwarning("Validation Error", "Please fix the User ID error!")
                return
        
        self._set_processing(True, "Camera Active")
        self.camera_running = True
        self.btn_capture.configure(state="normal")
        self.btn_stop_cam.configure(state="normal")
        self.btn_webcam.configure(state="disabled")
        
        threading.Thread(target=self._enroll_camera_loop, daemon=True).start()
    
    def _enroll_camera_loop(self):
        """Camera loop for enrollment"""
        try:
            self.camera.start()
            self.enroll_status.configure(text="✓ Camera started - Position your face and click Capture")
            
            while self.camera_running:
                ret, frame = self.camera.read_frame()
                if not ret:
                    continue
                
                faces = self.detector.detect_faces(frame)
                
                for face in faces:
                    x, y, w, h = face['box']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, "Face Detected", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                if not faces:
                    cv2.putText(frame, "No face detected", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                self.current_frame = frame.copy()
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb = cv2.resize(frame_rgb, (400, 300))
                img = Image.fromarray(frame_rgb)
                photo = ctk.CTkImage(img, size=(400, 300))
                
                self.enroll_camera_label.configure(image=photo, text="")
                self.enroll_camera_label.image = photo
                
                time.sleep(0.03)
            
            self.camera.stop()
        except Exception as e:
            self.enroll_status.configure(text=f"❌ Camera error: {str(e)}")
            self.camera.stop()
        finally:
            self._set_processing(False)
            self.btn_webcam.configure(state="normal")
            self.btn_upload.configure(state="normal")
    
    def _capture_frame(self):
        """Capture frame for enrollment - checks for duplicate faces first"""
        if self.current_frame is None:
            messagebox.showwarning("Error", "No camera frame available!")
            return
        
        faces = self.detector.detect_faces(self.current_frame)
        
        if not faces:
            messagebox.showwarning("No Face", "No face detected! Please position your face in the frame.")
            return
        
        face = self.detector.get_largest_face(faces)
        
        # CHECK FOR DUPLICATE FACE (only on first capture)
        if len(self.captured_faces) == 0:
            self.enroll_status.configure(text="🔍 Checking if face already exists...")
            self.update()
            
            # Generate embedding for captured face
            embedding = self.embedding_generator.generate_embedding(face['face_img'])
            
            if embedding is not None:
                # Check against all users in database with STRICT duplicate threshold
                from config import DUPLICATE_THRESHOLD
                result = self.verifier.verify_with_database(embedding, self.db)
                
                # Use stricter duplicate threshold (0.20) instead of regular (0.25)
                is_duplicate = result['distance'] < DUPLICATE_THRESHOLD
                
                if is_duplicate:
                    # Face already exists!
                    messagebox.showerror(
                        "❌ Duplicate Face Detected!",
                        f"This face is already registered as:\n\n"
                        f"Name: {result['user_name']}\n"
                        f"User ID: {result['user_id']}\n"
                        f"Match Distance: {result['distance']:.4f}\n\n"
                        f"You cannot register the same face twice."
                    )
                    self.enroll_status.configure(text="❌ Face already registered!")
                    return
                else:
                    self.enroll_status.configure(text="✅ New face - OK to enroll!")
        
        # Get/generate user ID
        user_id = self.entry_user_id.get().strip()
        if not user_id:
            user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.entry_user_id.delete(0, "end")
            self.entry_user_id.insert(0, user_id)
        
        user_dir = os.path.join(ENROLLED_IMAGES_DIR, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        img_path = os.path.join(user_dir, f"img_{len(self.captured_images) + 1}.jpg")
        cv2.imwrite(img_path, self.current_frame)
        
        self.captured_faces.append(face['face_img'])
        self.captured_images.append(img_path)
        
        count = len(self.captured_faces)
        self.enroll_progress.configure(text=f"📸 Captured: {count} images")
        self.enroll_progress_bar.set(min(count / 5, 1.0))
        self.enroll_status.configure(text=f"✓ Image {count} captured successfully!")
        
        if count >= 1:
            self.btn_save.configure(state="normal")
    
    def _enroll_from_files(self):
        """Enroll from image files"""
        if not self._validate_name():
            messagebox.showwarning("Validation Error", "Please enter a valid name first!")
            self.entry_name.focus()
            return
        
        file_paths = filedialog.askopenfilenames(
            title="Select Face Images (3-5 recommended)",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if not file_paths:
            return
        
        self._set_processing(True, "Processing images...")
        
        user_id = self.entry_user_id.get().strip()
        if not user_id:
            user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.entry_user_id.delete(0, "end")
            self.entry_user_id.insert(0, user_id)
        
        user_dir = os.path.join(ENROLLED_IMAGES_DIR, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        success_count = 0
        for file_path in file_paths:
            try:
                img = cv2.imread(file_path)
                if img is None:
                    continue
                
                faces = self.detector.detect_faces(img)
                if not faces:
                    continue
                
                face = self.detector.get_largest_face(faces)
                new_path = os.path.join(user_dir, f"img_{len(self.captured_images) + 1}.jpg")
                shutil.copy2(file_path, new_path)
                
                self.captured_faces.append(face['face_img'])
                self.captured_images.append(new_path)
                success_count += 1
            except Exception:
                continue
        
        self._set_processing(False)
        
        count = len(self.captured_faces)
        self.enroll_progress.configure(text=f"📸 Captured: {count} images")
        self.enroll_progress_bar.set(min(count / 5, 1.0))
        
        if success_count > 0:
            self.btn_save.configure(state="normal")
            self.enroll_status.configure(text=f"✓ Loaded {success_count} valid face images!")
            messagebox.showinfo("Success", f"Loaded {success_count} valid face images!")
        else:
            messagebox.showwarning("No Faces", "No valid face images found in selected files!")
    
    def _save_enrollment(self):
        """Save user enrollment"""
        if not self.captured_faces:
            messagebox.showerror("Error", "No face images captured!")
            return
        
        if not self._validate_name() or not self._validate_user_id():
            messagebox.showerror("Validation Error", "Please fix the form errors!")
            return
        
        user_id = self.entry_user_id.get().strip()
        name = self.entry_name.get().strip()
        
        if self.db.user_exists(user_id):
            messagebox.showerror("Error", f"User ID '{user_id}' already exists!")
            return
        
        self._set_processing(True, "Generating embeddings...")
        self.btn_save.configure(state="disabled")
        
        def process():
            try:
                embeddings = []
                for i, face_img in enumerate(self.captured_faces):
                    self.enroll_status.configure(text=f"Generating embedding {i+1}/{len(self.captured_faces)}...")
                    embedding = self.embedding_generator.generate_embedding(face_img)
                    if embedding is not None:
                        embeddings.append(embedding)
                
                if not embeddings:
                    self.after(0, lambda: messagebox.showerror("Error", "Could not generate face embeddings!"))
                    return
                
                self.db.add_user(user_id, name)
                for i, embedding in enumerate(embeddings):
                    img_path = self.captured_images[i] if i < len(self.captured_images) else None
                    self.db.add_embedding(user_id, embedding, img_path)
                
                self.after(0, lambda: self._enrollment_complete(user_id, name, len(embeddings)))
                
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to save user: {str(e)}"))
            finally:
                self.after(0, lambda: self._set_processing(False))
        
        threading.Thread(target=process, daemon=True).start()
    
    def _enrollment_complete(self, user_id, name, count):
        """Handle enrollment completion"""
        messagebox.showinfo(
            "Success",
            f"User enrolled successfully!\n\n"
            f"👤 Name: {name}\n"
            f"🆔 ID: {user_id}\n"
            f"📊 Embeddings: {count}"
        )
        self._stop_camera()
        self._reset_enrollment()
        self._update_stats()
    
    # === Verification Methods ===
    
    def _start_verify_camera(self):
        """Start camera for verification"""
        users = self.db.get_all_users()
        if not users:
            messagebox.showwarning("No Users", "No users enrolled yet! Please enroll a user first.")
            return
        
        self.camera_running = True
        self.btn_stop_verify.configure(state="normal")
        self.btn_live_verify.configure(state="disabled")
        self.verifier.reset_voting()
        self._set_processing(True, "Verifying...")
        
        threading.Thread(target=self._verify_camera_loop, daemon=True).start()
    
    def _verify_camera_loop(self):
        """Camera loop for verification - FIXED for performance"""
        try:
            self.camera.start()
            
            frame_count = 0
            process_every = 10  # Process every 10th frame (reduce CPU load)
            last_result = None
            last_box = None
            last_color = (128, 128, 128)
            last_update_time = 0
            
            while self.camera_running:
                ret, frame = self.camera.read_frame()
                if not ret:
                    time.sleep(0.01)
                    continue
                
                frame_count += 1
                current_time = time.time()
                
                # Only process every Nth frame AND at least 300ms apart
                should_process = (frame_count % process_every == 0) and (current_time - last_update_time > 0.3)
                
                if should_process:
                    last_update_time = current_time
                    
                    try:
                        faces = self.detector.detect_faces(frame)
                        
                        if faces:
                            face = self.detector.get_largest_face(faces)
                            x, y, w, h = face['box']
                            last_box = (x, y, w, h)
                            
                            embedding = self.embedding_generator.generate_embedding(face['face_img'])
                            
                            if embedding is not None:
                                result = self.verifier.verify_with_database(embedding, self.db)
                                result = self.verifier.verify_with_voting(result)
                                last_result = result
                                
                                if result['verified']:
                                    last_color = (0, 255, 0)
                                    result_text = f"✅ VERIFIED: {result['user_name']} ({result['confidence']:.1f}%)"
                                    text_color = "green"
                                    
                                    # Show popup once when fully verified (voting complete)
                                    voting_status = result.get('voting_status', '')
                                    if voting_status == 'complete' and not getattr(self, '_popup_shown', False):
                                        self._popup_shown = True
                                        # Stop camera and show popup
                                        self.camera_running = False
                                        user_name = result.get('user_name', 'Unknown')
                                        confidence = result.get('confidence', 0)
                                        self.after(100, lambda: messagebox.showinfo(
                                            "✅ ACCESS GRANTED",
                                            f"Welcome back, {user_name}!\n\nConfidence: {confidence:.1f}%"
                                        ))
                                else:
                                    last_color = (0, 0, 255)
                                    result_text = f"❌ NOT VERIFIED ({result['confidence']:.1f}%)"
                                    text_color = "red"
                                
                                # Thread-safe UI update
                                self.after(0, lambda t=result_text, c=text_color: 
                                    self.verify_result.configure(text=t, text_color=c))
                        else:
                            last_box = None
                            last_result = None
                            self._popup_shown = False
                            self.after(0, lambda: self.verify_result.configure(
                                text="🔍 No face detected", text_color="orange"))
                            self.verifier.reset_voting()
                    except Exception as e:
                        print(f"Processing error: {e}")
                
                # Draw cached box on every frame
                display_frame = frame.copy()
                if last_box:
                    x, y, w, h = last_box
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), last_color, 3)
                
                # Convert for display
                try:
                    frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    frame_rgb = cv2.resize(frame_rgb, (480, 360))
                    img = Image.fromarray(frame_rgb)
                    photo = ctk.CTkImage(img, size=(480, 360))
                    
                    # Thread-safe image update
                    self.after(0, lambda p=photo: self._update_verify_image(p))
                except Exception:
                    pass
                
                time.sleep(0.02)  # ~50 FPS max display rate
            
            self.camera.stop()
        except Exception as e:
            print(f"Camera error: {e}")
            try:
                self.camera.stop()
            except:
                pass
        finally:
            self.after(0, self._verify_cleanup)
    
    def _update_verify_image(self, photo):
        """Thread-safe image update"""
        try:
            self.verify_camera_label.configure(image=photo, text="")
            self.verify_camera_label.image = photo
        except:
            pass
    
    def _verify_cleanup(self):
        """Cleanup after verification"""
        self._set_processing(False)
        self.btn_live_verify.configure(state="normal")
        self.btn_img_verify.configure(state="normal")
    
    def _verify_from_image(self):
        """Verify from image file"""
        users = self.db.get_all_users()
        if not users:
            messagebox.showwarning("No Users", "No users enrolled yet!")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Image to Verify",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        self._set_processing(True, "Processing image...")
        
        try:
            img = cv2.imread(file_path)
            if img is None:
                messagebox.showerror("Error", "Could not read image file!")
                return
            
            faces = self.detector.detect_faces(img)
            
            if not faces:
                messagebox.showerror("No Face", "No face detected in the image!")
                return
            
            face = self.detector.get_largest_face(faces)
            embedding = self.embedding_generator.generate_embedding(face['face_img'])
            
            if embedding is None:
                messagebox.showerror("Error", "Could not process face!")
                return
            
            result = self.verifier.verify_with_database(embedding, self.db)
            
            x, y, w, h = face['box']
            if result['verified']:
                color = (0, 255, 0)
                self.verify_result.configure(
                    text=f"✅ VERIFIED: {result['user_name']} ({result['confidence']:.1f}%)",
                    text_color="green"
                )
            else:
                color = (0, 0, 255)
                self.verify_result.configure(
                    text=f"❌ NOT VERIFIED ({result['confidence']:.1f}%)",
                    text_color="red"
                )
            
            # Show popup
            self._show_verification_popup(result)
            
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)
            
            frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = frame_rgb.shape[:2]
            scale = min(500/w, 375/h)
            new_size = (int(w*scale), int(h*scale))
            frame_rgb = cv2.resize(frame_rgb, new_size)
            
            img_pil = Image.fromarray(frame_rgb)
            photo = ctk.CTkImage(img_pil, size=new_size)
            
            self.verify_camera_label.configure(image=photo, text="")
            self.verify_camera_label.image = photo
            
        except Exception as e:
            messagebox.showerror("Error", f"Verification failed: {str(e)}")
        finally:
            self._set_processing(False)
    
    def _show_verification_popup(self, result):
        """Show professional verification popup"""
        print(f"=== POPUP TRIGGERED === Result: {result}")  # Debug
        
        # Stop camera FIRST if verified
        if result['verified']:
            print("Stopping camera...")
            self._stop_verification()
            
            # Show simple message first
            user_name = result.get('user_name', 'Unknown')
            confidence = result.get('confidence', 0)
            
            # Use simple messagebox as backup (guaranteed to work)
            messagebox.showinfo(
                "✅ ACCESS GRANTED",
                f"Welcome back, {user_name}!\n\nConfidence: {confidence:.1f}%"
            )
    
    # === User Management Methods ===
    
    def _update_user_list(self):
        """Update user list"""
        for widget in self.users_list_frame.winfo_children():
            widget.destroy()
        
        users = self.db.get_all_users()
        self.all_users_data = users
        
        if not users:
            ctk.CTkLabel(
                self.users_list_frame,
                text="📭 No users enrolled yet.\n\nGo to 'Enroll User' to add users.",
                font=ctk.CTkFont(size=14)
            ).pack(pady=50)
            return
        
        self._display_users(users)
    
    def _display_users(self, users):
        """Display user list"""
        for widget in self.users_list_frame.winfo_children():
            widget.destroy()
        
        for user in users:
            count = self.db.get_embedding_count(user['user_id'])
            
            user_frame = ctk.CTkFrame(self.users_list_frame)
            user_frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(
                user_frame,
                text=f"👤 {user['name']}",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(side="left", padx=10, pady=10)
            
            ctk.CTkLabel(
                user_frame,
                text=f"ID: {user['user_id']} | 📊 {count} embeddings",
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10)
            
            ctk.CTkButton(
                user_frame, text="🗑 Delete",
                width=80, height=30,
                fg_color="red", hover_color="darkred",
                command=lambda uid=user['user_id'], name=user['name']: self._delete_user(uid, name)
            ).pack(side="right", padx=10, pady=5)
    
    def _filter_users(self, event=None):
        """Filter users by search term"""
        search = self.search_entry.get().strip().lower()
        
        if not search:
            self._display_users(self.all_users_data)
            return
        
        filtered = [u for u in self.all_users_data 
                   if search in u['name'].lower() or search in u['user_id'].lower()]
        self._display_users(filtered)
    
    def _delete_user(self, user_id, name):
        """Delete a user"""
        if not messagebox.askyesno("Confirm Delete", 
            f"Are you sure you want to delete:\n\n👤 {name}\n🆔 {user_id}\n\nThis action cannot be undone!"):
            return
        
        try:
            user_dir = os.path.join(ENROLLED_IMAGES_DIR, user_id)
            if os.path.exists(user_dir):
                shutil.rmtree(user_dir)
            
            self.db.delete_user(user_id)
            self._update_user_list()
            self._update_stats()
            messagebox.showinfo("Deleted", f"User '{name}' has been deleted.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete user: {str(e)}")
    
    def _stop_camera(self):
        """Stop camera"""
        self.camera_running = False
        self.btn_capture.configure(state="disabled")
        self.btn_stop_cam.configure(state="disabled")
        self.btn_stop_verify.configure(state="disabled")
        time.sleep(0.1)
        try:
            self.camera.stop()
        except:
            pass
    
    def _update_stats(self):
        """Update statistics"""
        stats = self.db.get_statistics()
        self.lbl_stats.configure(text=f"👥 Users: {stats['total_users']}\n📊 Embeddings: {stats['total_embeddings']}")
    
    def _on_closing(self):
        """Handle window close"""
        self._stop_camera()
        self.destroy()


def main():
    """Main entry point"""
    app = FaceVerificationApp()
    app.mainloop()


if __name__ == "__main__":
    main()
