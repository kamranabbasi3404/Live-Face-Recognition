"""
Utility Helper Functions
"""
import os
import cv2
import numpy as np
from datetime import datetime


def generate_user_id():
    """
    Generate a unique user ID based on timestamp
    
    Returns:
        str: Unique user ID
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"user_{timestamp}"


def save_image(image, directory, filename=None):
    """
    Save image to directory
    
    Args:
        image: Image to save (numpy array)
        directory: Target directory
        filename: Optional filename (auto-generated if not provided)
        
    Returns:
        str: Full path to saved image
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"img_{timestamp}.jpg"
    
    filepath = os.path.join(directory, filename)
    cv2.imwrite(filepath, image)
    
    return filepath


def load_images_from_directory(directory):
    """
    Load all images from a directory
    
    Args:
        directory: Path to directory
        
    Returns:
        list: List of loaded images
    """
    images = []
    
    if not os.path.exists(directory):
        return images
    
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(valid_extensions):
            filepath = os.path.join(directory, filename)
            img = cv2.imread(filepath)
            if img is not None:
                images.append(img)
    
    return images


def resize_image(image, max_size=800):
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: Input image
        max_size: Maximum dimension size
        
    Returns:
        Resized image
    """
    h, w = image.shape[:2]
    
    if max(h, w) <= max_size:
        return image
    
    if h > w:
        new_h = max_size
        new_w = int(w * max_size / h)
    else:
        new_w = max_size
        new_h = int(h * max_size / w)
    
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def normalize_image(image):
    """
    Normalize image values to 0-1 range
    
    Args:
        image: Input image
        
    Returns:
        Normalized image (float32)
    """
    return image.astype(np.float32) / 255.0


def enhance_image(image):
    """
    Enhance image quality (histogram equalization)
    
    Args:
        image: Input BGR image
        
    Returns:
        Enhanced image
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    
    # Convert back to BGR
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    return enhanced


def calculate_image_hash(image):
    """
    Calculate a simple hash for image comparison
    
    Args:
        image: Input image
        
    Returns:
        str: Hash string
    """
    # Resize to small size
    resized = cv2.resize(image, (8, 8), interpolation=cv2.INTER_AREA)
    
    # Convert to grayscale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    
    # Calculate average
    avg = gray.mean()
    
    # Create hash based on pixel comparisons
    hash_bits = gray > avg
    hash_str = ''.join(['1' if b else '0' for b in hash_bits.flatten()])
    
    return hex(int(hash_str, 2))


def format_timestamp(dt=None):
    """
    Format datetime as readable string
    
    Args:
        dt: Datetime object (uses current time if None)
        
    Returns:
        str: Formatted timestamp
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def clear_console():
    """Clear console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_menu(title, options):
    """
    Print a formatted menu
    
    Args:
        title: Menu title
        options: List of (key, description) tuples
    """
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)
    
    for key, desc in options:
        print(f"  [{key}] {desc}")
    
    print("=" * 50)


def get_user_input(prompt, valid_options=None):
    """
    Get user input with validation
    
    Args:
        prompt: Input prompt
        valid_options: Optional list of valid options
        
    Returns:
        str: User input
    """
    while True:
        user_input = input(prompt).strip()
        
        if valid_options is None or user_input in valid_options:
            return user_input
        
        print(f"Invalid input. Please choose from: {', '.join(valid_options)}")
