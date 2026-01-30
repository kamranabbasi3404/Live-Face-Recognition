"""
Display Module - UI display helpers for OpenCV windows
"""
import cv2
import numpy as np
from config import (
    BOX_COLOR_VERIFIED, BOX_COLOR_NOT_VERIFIED, BOX_COLOR_DETECTING,
    BOX_THICKNESS, FONT_SCALE, FONT_THICKNESS, WINDOW_NAME
)


class Display:
    """Handles UI display with OpenCV"""
    
    def __init__(self, window_name=WINDOW_NAME):
        """
        Initialize display
        
        Args:
            window_name: Name of the OpenCV window
        """
        self.window_name = window_name
        self.font = cv2.FONT_HERSHEY_SIMPLEX
    
    def draw_face_box(self, frame, box, status='detecting', label=None, confidence=None):
        """
        Draw bounding box around face
        
        Args:
            frame: Image frame
            box: Face box (x, y, w, h)
            status: 'verified', 'not_verified', or 'detecting'
            label: Optional label text
            confidence: Optional confidence percentage
        """
        x, y, w, h = box
        
        # Choose color based on status
        if status == 'verified':
            color = BOX_COLOR_VERIFIED
        elif status == 'not_verified':
            color = BOX_COLOR_NOT_VERIFIED
        else:
            color = BOX_COLOR_DETECTING
        
        # Draw rectangle
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, BOX_THICKNESS)
        
        # Draw corner accents for modern look
        corner_length = min(20, w // 4, h // 4)
        cv2.line(frame, (x, y), (x + corner_length, y), color, BOX_THICKNESS + 1)
        cv2.line(frame, (x, y), (x, y + corner_length), color, BOX_THICKNESS + 1)
        cv2.line(frame, (x + w, y), (x + w - corner_length, y), color, BOX_THICKNESS + 1)
        cv2.line(frame, (x + w, y), (x + w, y + corner_length), color, BOX_THICKNESS + 1)
        cv2.line(frame, (x, y + h), (x + corner_length, y + h), color, BOX_THICKNESS + 1)
        cv2.line(frame, (x, y + h), (x, y + h - corner_length), color, BOX_THICKNESS + 1)
        cv2.line(frame, (x + w, y + h), (x + w - corner_length, y + h), color, BOX_THICKNESS + 1)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_length), color, BOX_THICKNESS + 1)
        
        # Draw label
        if label:
            label_text = label
            if confidence is not None:
                label_text += f" ({confidence:.1f}%)"
            
            # Background for text
            (text_w, text_h), _ = cv2.getTextSize(label_text, self.font, FONT_SCALE, FONT_THICKNESS)
            cv2.rectangle(frame, (x, y - text_h - 10), (x + text_w + 10, y), color, -1)
            cv2.putText(frame, label_text, (x + 5, y - 5),
                       self.font, FONT_SCALE, (255, 255, 255), FONT_THICKNESS)
    
    def draw_status(self, frame, text, position='top', color=(255, 255, 255)):
        """
        Draw status text on frame
        
        Args:
            frame: Image frame
            text: Status text
            position: 'top', 'bottom', or tuple (x, y)
            color: Text color (B, G, R)
        """
        if isinstance(position, str):
            if position == 'top':
                pos = (10, 30)
            else:  # bottom
                pos = (10, frame.shape[0] - 20)
        else:
            pos = position
        
        # Draw text with shadow for visibility
        cv2.putText(frame, text, (pos[0] + 2, pos[1] + 2),
                   self.font, FONT_SCALE, (0, 0, 0), FONT_THICKNESS + 1)
        cv2.putText(frame, text, pos,
                   self.font, FONT_SCALE, color, FONT_THICKNESS)
    
    def draw_fps(self, frame, fps):
        """
        Draw FPS counter
        
        Args:
            frame: Image frame
            fps: Current FPS value
        """
        fps_text = f"FPS: {fps:.1f}"
        pos = (frame.shape[1] - 100, 30)
        
        cv2.putText(frame, fps_text, (pos[0] + 1, pos[1] + 1),
                   self.font, 0.5, (0, 0, 0), 1)
        cv2.putText(frame, fps_text, pos,
                   self.font, 0.5, (0, 255, 0), 1)
    
    def draw_verification_result(self, frame, result, user_name=None):
        """
        Draw verification result overlay
        
        Args:
            frame: Image frame
            result: Verification result dictionary
            user_name: Name of verified user
        """
        verified = result.get('verified', False)
        confidence = result.get('confidence', 0)
        
        # Status text
        if verified:
            status_text = f"VERIFIED: {user_name}" if user_name else "VERIFIED"
            status_color = BOX_COLOR_VERIFIED
        else:
            status_text = "NOT VERIFIED"
            status_color = BOX_COLOR_NOT_VERIFIED
        
        # Draw semi-transparent overlay at bottom
        overlay = frame.copy()
        h, w = frame.shape[:2]
        cv2.rectangle(overlay, (0, h - 80), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Draw status
        cv2.putText(frame, status_text, (20, h - 50),
                   self.font, 0.9, status_color, 2)
        
        # Draw confidence bar
        bar_width = 200
        bar_height = 15
        bar_x = 20
        bar_y = h - 25
        
        # Background bar
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     (100, 100, 100), -1)
        
        # Filled bar
        fill_width = int(bar_width * confidence / 100)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height),
                     status_color, -1)
        
        # Confidence text
        conf_text = f"{confidence:.1f}%"
        cv2.putText(frame, conf_text, (bar_x + bar_width + 10, bar_y + 12),
                   self.font, 0.5, (255, 255, 255), 1)
    
    def draw_enrollment_progress(self, frame, current, total):
        """
        Draw enrollment progress
        
        Args:
            frame: Image frame
            current: Current number of captured images
            total: Total required images
        """
        h, w = frame.shape[:2]
        
        # Draw overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - 60), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Progress text
        progress_text = f"Captured: {current}/{total} images"
        cv2.putText(frame, progress_text, (20, h - 35),
                   self.font, 0.7, (255, 255, 255), 2)
        
        # Instructions
        inst_text = "Press SPACE to capture, Q when done"
        cv2.putText(frame, inst_text, (20, h - 10),
                   self.font, 0.5, (200, 200, 200), 1)
    
    def draw_quality_warning(self, frame, message):
        """
        Draw quality warning message
        
        Args:
            frame: Image frame
            message: Warning message
        """
        h, w = frame.shape[:2]
        
        # Warning background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 50), (0, 0, 150), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Warning text
        cv2.putText(frame, f"Warning: {message}", (10, 30),
                   self.font, 0.6, (255, 255, 255), 2)
    
    def draw_instructions(self, frame, instructions):
        """
        Draw list of instructions
        
        Args:
            frame: Image frame
            instructions: List of instruction strings
        """
        y_offset = 60
        for inst in instructions:
            cv2.putText(frame, inst, (10, y_offset),
                       self.font, 0.5, (255, 255, 255), 1)
            y_offset += 25
    
    def show(self, frame):
        """
        Display frame in window
        
        Args:
            frame: Image frame
        """
        cv2.imshow(self.window_name, frame)
    
    def wait_key(self, delay=1):
        """
        Wait for key press
        
        Args:
            delay: Wait time in ms
            
        Returns:
            int: Key code or -1
        """
        return cv2.waitKey(delay) & 0xFF
    
    def close(self):
        """Close all windows"""
        cv2.destroyAllWindows()


def test_display():
    """Test display functions"""
    import numpy as np
    
    display = Display("Display Test")
    
    # Create test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = (50, 50, 50)  # Dark gray background
    
    # Draw test elements
    display.draw_face_box(frame, (200, 100, 200, 250), 'verified', 'Test User', 95.5)
    display.draw_fps(frame, 29.7)
    display.draw_status(frame, "Testing Display Module", 'top')
    
    # Draw verification result
    result = {'verified': True, 'confidence': 95.5}
    display.draw_verification_result(frame, result, 'Test User')
    
    display.show(frame)
    print("Press any key to close...")
    cv2.waitKey(0)
    display.close()


if __name__ == "__main__":
    test_display()
