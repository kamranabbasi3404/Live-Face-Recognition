"""
Configuration settings for Live Face Verification System
"""
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Camera settings
CAMERA_INDEX = 0  # Default camera (0 = built-in webcam)
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
TARGET_FPS = 30

# Face detection settings (adjusted for low-quality cameras)
FACE_DETECTOR_BACKEND = "opencv"  # Options: opencv, mtcnn, retinaface, ssd
MIN_FACE_SIZE = 50  # Minimum face size in pixels (lowered for low-res cameras)
FACE_DETECTION_CONFIDENCE = 0.4

# Embedding settings - Using Facenet512 for BETTER accuracy (512-dim embeddings)
EMBEDDING_MODEL = "Facenet512"  # More detailed than Facenet (128-dim)
DISTANCE_METRIC = "cosine"  # Options: cosine, euclidean, euclidean_l2

# Verification settings - STRICT threshold
VERIFICATION_THRESHOLD = 0.25  # Very strict - only close matches pass
VERIFICATION_FRAMES = 5  # Number of frames for majority voting
VERIFICATION_MAJORITY = 3  # Minimum matches needed for verification

# Duplicate detection - even stricter
DUPLICATE_THRESHOLD = 0.20  # Super strict for duplicate check

# Quality check settings (DISABLED - accept any quality)
BLUR_THRESHOLD = 1  # Accept almost any blur level
BRIGHTNESS_MIN = 1  # Accept very dark images
BRIGHTNESS_MAX = 255  # Accept very bright images

# Liveness detection settings
LIVENESS_ENABLED = True
EAR_THRESHOLD = 0.25  # Eye Aspect Ratio threshold for blink detection
BLINK_CONSECUTIVE_FRAMES = 2  # Frames to confirm a blink

# Database settings
DATABASE_PATH = os.path.join(BASE_DIR, "database", "face_db.sqlite")

# Enrolled images directory
ENROLLED_IMAGES_DIR = os.path.join(BASE_DIR, "enrolled_images")

# Ensure directories exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(ENROLLED_IMAGES_DIR, exist_ok=True)

# UI settings
WINDOW_NAME = "Live Face Verification"
BOX_COLOR_VERIFIED = (0, 255, 0)  # Green
BOX_COLOR_NOT_VERIFIED = (0, 0, 255)  # Red
BOX_COLOR_DETECTING = (255, 255, 0)  # Yellow
BOX_THICKNESS = 2
FONT_SCALE = 0.7
FONT_THICKNESS = 2
