"""
Face Detector Module - Handles face detection, alignment, and quality checks
"""
import cv2
import numpy as np
from config import (
    MIN_FACE_SIZE, FACE_DETECTION_CONFIDENCE, FACE_DETECTOR_BACKEND,
    BLUR_THRESHOLD, BRIGHTNESS_MIN, BRIGHTNESS_MAX
)


class FaceDetector:
    """Handles face detection and quality validation"""
    
    def __init__(self, backend=FACE_DETECTOR_BACKEND):
        """
        Initialize face detector
        
        Args:
            backend: Detection backend (opencv, mtcnn, retinaface, ssd)
        """
        self.backend = backend
        self.face_cascade = None
        
        # Initialize OpenCV cascade for fast detection
        if backend == "opencv":
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
    
    def detect_faces(self, frame):
        """
        Detect faces in a frame
        
        Args:
            frame: BGR image (numpy array)
            
        Returns:
            list: List of face dictionaries with 'box', 'confidence', 'face_img'
        """
        if frame is None:
            return []
        
        faces = []
        
        if self.backend == "opencv":
            faces = self._detect_opencv(frame)
        else:
            # Use DeepFace for other backends
            faces = self._detect_deepface(frame)
        
        return faces
    
    def _detect_opencv(self, frame):
        """Detect faces using OpenCV Haar Cascade"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        detections = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(MIN_FACE_SIZE, MIN_FACE_SIZE),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        faces = []
        for (x, y, w, h) in detections:
            # Add padding around face
            padding = int(0.1 * max(w, h))
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(frame.shape[1], x + w + padding)
            y2 = min(frame.shape[0], y + h + padding)
            
            face_img = frame[y1:y2, x1:x2]
            
            faces.append({
                'box': (x, y, w, h),
                'box_padded': (x1, y1, x2 - x1, y2 - y1),
                'confidence': 1.0,  # OpenCV doesn't provide confidence
                'face_img': face_img
            })
        
        return faces
    
    def _detect_deepface(self, frame):
        """Detect faces using DeepFace"""
        try:
            from deepface import DeepFace
            
            result = DeepFace.extract_faces(
                img_path=frame,
                detector_backend=self.backend,
                enforce_detection=False,
                align=True
            )
            
            faces = []
            for face_data in result:
                if face_data['confidence'] >= FACE_DETECTION_CONFIDENCE:
                    region = face_data['facial_area']
                    x, y, w, h = region['x'], region['y'], region['w'], region['h']
                    
                    # Ensure coordinates are valid
                    x = max(0, x)
                    y = max(0, y)
                    x2 = min(frame.shape[1], x + w)
                    y2 = min(frame.shape[0], y + h)
                    
                    face_img = frame[y:y2, x:x2]
                    
                    if face_img.size > 0:
                        faces.append({
                            'box': (x, y, w, h),
                            'confidence': face_data['confidence'],
                            'face_img': face_img
                        })
            
            return faces
            
        except Exception as e:
            print(f"DeepFace detection error: {e}")
            return []
    
    def check_quality(self, face_img):
        """
        Check face image quality
        
        Args:
            face_img: Face image (numpy array)
            
        Returns:
            dict: Quality metrics and overall pass/fail
        """
        if face_img is None or face_img.size == 0:
            return {'passed': False, 'reason': 'Invalid image'}
        
        # Convert to grayscale for analysis
        if len(face_img.shape) == 3:
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_img
        
        # Check blur (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        is_blurry = blur_score < BLUR_THRESHOLD
        
        # Check brightness
        brightness = np.mean(gray)
        is_dark = brightness < BRIGHTNESS_MIN
        is_bright = brightness > BRIGHTNESS_MAX
        
        # Check size
        is_small = min(face_img.shape[:2]) < MIN_FACE_SIZE
        
        # Determine overall quality
        passed = not (is_blurry or is_dark or is_bright or is_small)
        
        reasons = []
        if is_blurry:
            reasons.append('Too blurry')
        if is_dark:
            reasons.append('Too dark')
        if is_bright:
            reasons.append('Too bright')
        if is_small:
            reasons.append('Face too small')
        
        return {
            'passed': passed,
            'blur_score': blur_score,
            'brightness': brightness,
            'size': min(face_img.shape[:2]),
            'reason': ', '.join(reasons) if reasons else 'Good quality'
        }
    
    def align_face(self, face_img, target_size=(224, 224)):
        """
        Align and resize face image
        
        Args:
            face_img: Face image (numpy array)
            target_size: Output size tuple
            
        Returns:
            Aligned face image
        """
        if face_img is None or face_img.size == 0:
            return None
        
        # Resize to target size
        aligned = cv2.resize(face_img, target_size, interpolation=cv2.INTER_AREA)
        
        return aligned
    
    def get_largest_face(self, faces):
        """
        Get the largest face from detected faces
        
        Args:
            faces: List of face dictionaries
            
        Returns:
            Largest face dictionary or None
        """
        if not faces:
            return None
        
        largest = max(faces, key=lambda f: f['box'][2] * f['box'][3])
        return largest


def test_face_detector():
    """Test face detector with webcam"""
    import cv2
    from camera import Camera
    
    detector = FaceDetector()
    
    with Camera() as cam:
        print("Face detector test - Press 'q' to quit")
        
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                break
            
            faces = detector.detect_faces(frame)
            
            for face in faces:
                x, y, w, h = face['box']
                quality = detector.check_quality(face['face_img'])
                
                # Draw box
                color = (0, 255, 0) if quality['passed'] else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                # Draw quality info
                text = f"Quality: {quality['reason']}"
                cv2.putText(frame, text, (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            cv2.imshow("Face Detection Test", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()


if __name__ == "__main__":
    test_face_detector()
