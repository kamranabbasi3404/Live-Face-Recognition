"""
Camera Module - Handles video capture from webcam
"""
import cv2
import time
import os
from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, TARGET_FPS

# Suppress OpenCV warnings
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"


class Camera:
    """Handles webcam capture operations"""
    
    def __init__(self, camera_index=CAMERA_INDEX, width=CAMERA_WIDTH, height=CAMERA_HEIGHT):
        """
        Initialize camera
        
        Args:
            camera_index: Camera device index (0 for default webcam)
            width: Frame width
            height: Frame height
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.start_time = None
        
    def start(self):
        """Start the camera capture"""
        # Use default backend (most reliable)
        self.cap = cv2.VideoCapture(self.camera_index)
        
        # Wait a moment for camera to initialize
        time.sleep(0.5)
        
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open camera at index {self.camera_index}.\n"
                "Please check:\n"
                "  1. Webcam is connected\n"
                "  2. No other app is using the camera\n"
                "  3. Camera permissions are enabled"
            )
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
        
        # Warm up - read a few frames to stabilize
        for _ in range(5):
            self.cap.read()
        
        self.start_time = time.time()
        self.frame_count = 0
        
        print("Camera started successfully!")
        return True
    
    def read_frame(self):
        """
        Read a frame from the camera
        
        Returns:
            tuple: (success, frame) where success is bool and frame is numpy array
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None
        
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_count += 1
            # Calculate FPS every 30 frames
            if self.frame_count % 30 == 0:
                elapsed = time.time() - self.start_time
                self.fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        return ret, frame
    
    def get_fps(self):
        """Get current FPS"""
        return self.fps
    
    def stop(self):
        """Stop and release the camera"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def is_opened(self):
        """Check if camera is opened"""
        return self.cap is not None and self.cap.isOpened()
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        return False


def test_camera():
    """Test camera functionality"""
    print("Testing camera...")
    
    with Camera() as cam:
        print(f"Camera opened successfully")
        
        for i in range(100):
            ret, frame = cam.read_frame()
            if ret:
                cv2.imshow("Camera Test", frame)
                
                # Display FPS
                fps = cam.get_fps()
                if fps > 0:
                    print(f"\rFPS: {fps:.2f}", end="")
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        cv2.destroyAllWindows()
    
    print("\nCamera test complete")


if __name__ == "__main__":
    test_camera()
