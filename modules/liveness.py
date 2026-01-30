"""
Liveness Detection Module - Detects blinks and head movement for anti-spoofing
"""
import cv2
import numpy as np
from collections import deque
from config import EAR_THRESHOLD, BLINK_CONSECUTIVE_FRAMES


class LivenessDetector:
    """Detects liveness through blink detection and head movement"""
    
    def __init__(self):
        """Initialize liveness detector"""
        self.blink_counter = 0
        self.total_blinks = 0
        self.ear_history = deque(maxlen=30)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
    
    def calculate_ear(self, eye_points):
        """
        Calculate Eye Aspect Ratio (EAR)
        
        EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
        
        Args:
            eye_points: Array of 6 eye landmark points
            
        Returns:
            float: Eye aspect ratio
        """
        # Compute euclidean distances
        A = np.linalg.norm(eye_points[1] - eye_points[5])
        B = np.linalg.norm(eye_points[2] - eye_points[4])
        C = np.linalg.norm(eye_points[0] - eye_points[3])
        
        ear = (A + B) / (2.0 * C + 1e-6)
        return ear
    
    def detect_eyes(self, face_img):
        """
        Detect eyes in face image
        
        Args:
            face_img: Face image (numpy array)
            
        Returns:
            list: List of eye regions [(x, y, w, h), ...]
        """
        if face_img is None or face_img.size == 0:
            return []
        
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY) if len(face_img.shape) == 3 else face_img
        
        eyes = self.eye_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20, 20)
        )
        
        return eyes
    
    def detect_blink(self, face_img):
        """
        Detect if eyes are blinking
        
        Args:
            face_img: Face image
            
        Returns:
            dict: Blink detection result
        """
        eyes = self.detect_eyes(face_img)
        
        # Calculate eye openness based on detected eyes
        if len(eyes) >= 2:
            # Eyes are open
            avg_height = np.mean([e[3] for e in eyes])
            avg_width = np.mean([e[2] for e in eyes])
            ear_approx = avg_height / (avg_width + 1e-6)
        elif len(eyes) == 1:
            # One eye detected (possible partial blink)
            ear_approx = eyes[0][3] / (eyes[0][2] + 1e-6)
        else:
            # No eyes detected (eyes closed or face issue)
            ear_approx = 0.0
        
        self.ear_history.append(ear_approx)
        
        # Detect blink (EAR drops below threshold)
        if ear_approx < EAR_THRESHOLD:
            self.blink_counter += 1
        else:
            if self.blink_counter >= BLINK_CONSECUTIVE_FRAMES:
                self.total_blinks += 1
            self.blink_counter = 0
        
        return {
            'eyes_detected': len(eyes),
            'ear': ear_approx,
            'is_blinking': self.blink_counter >= BLINK_CONSECUTIVE_FRAMES,
            'total_blinks': self.total_blinks,
            'eyes_open': len(eyes) >= 2 and ear_approx > EAR_THRESHOLD
        }
    
    def check_liveness(self, face_img, require_blink=True):
        """
        Check if the face is from a live person
        
        Args:
            face_img: Face image
            require_blink: Whether to require blink detection
            
        Returns:
            dict: Liveness check result
        """
        blink_result = self.detect_blink(face_img)
        
        # Basic liveness: eyes must be detected
        eyes_present = blink_result['eyes_detected'] >= 1
        
        # Liveness passes if:
        # 1. Eyes are present AND
        # 2. Either blink detected OR blink not required
        is_live = eyes_present and (
            not require_blink or 
            blink_result['total_blinks'] > 0
        )
        
        return {
            'is_live': is_live,
            'eyes_detected': blink_result['eyes_detected'],
            'blinks_detected': blink_result['total_blinks'],
            'eyes_open': blink_result['eyes_open'],
            'reason': self._get_liveness_reason(blink_result, require_blink)
        }
    
    def _get_liveness_reason(self, blink_result, require_blink):
        """Get human-readable liveness status"""
        if blink_result['eyes_detected'] < 1:
            return "No eyes detected"
        if require_blink and blink_result['total_blinks'] == 0:
            return "Please blink to verify liveness"
        if blink_result['total_blinks'] > 0:
            return f"Liveness confirmed ({blink_result['total_blinks']} blinks)"
        return "Eyes detected"
    
    def reset(self):
        """Reset liveness detection state"""
        self.blink_counter = 0
        self.total_blinks = 0
        self.ear_history.clear()
    
    def get_instructions(self):
        """Get user instructions for liveness check"""
        if self.total_blinks == 0:
            return "Please blink to confirm liveness"
        return "Liveness confirmed!"


def test_liveness():
    """Test liveness detection with webcam"""
    from camera import Camera
    from face_detector import FaceDetector
    
    detector = FaceDetector()
    liveness = LivenessDetector()
    
    with Camera() as cam:
        print("Liveness test - Blink to test detection. Press 'q' to quit, 'r' to reset")
        
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                break
            
            faces = detector.detect_faces(frame)
            
            for face in faces:
                x, y, w, h = face['box']
                
                # Check liveness
                result = liveness.check_liveness(face['face_img'])
                
                # Draw face box
                color = (0, 255, 0) if result['is_live'] else (0, 255, 255)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                # Draw info
                info = f"Blinks: {result['blinks_detected']} | {result['reason']}"
                cv2.putText(frame, info, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Draw instructions
            cv2.putText(frame, liveness.get_instructions(), (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow("Liveness Test", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                liveness.reset()
                print("Liveness detector reset")
        
        cv2.destroyAllWindows()


if __name__ == "__main__":
    test_liveness()
