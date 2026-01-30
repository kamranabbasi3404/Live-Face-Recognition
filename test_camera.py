"""
Simple Camera Test Script
Run this to verify your webcam works with OpenCV
"""
import cv2
import sys

def test_camera():
    print("=" * 50)
    print("       CAMERA TEST")
    print("=" * 50)
    print("\nTrying to open camera...")
    
    # Try DirectShow backend for Windows
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("DirectShow failed, trying default backend...")
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("\n[ERROR] Could not open camera!")
        print("Please check:")
        print("  1. Webcam is connected")
        print("  2. No other app is using the camera")
        print("  3. Camera drivers are installed")
        return False
    
    print("[SUCCESS] Camera opened!")
    print("\nCamera Properties:")
    print(f"  Width: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}")
    print(f"  Height: {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
    print(f"  FPS: {cap.get(cv2.CAP_PROP_FPS)}")
    
    print("\n" + "-" * 50)
    print("Press 'Q' to quit the test")
    print("-" * 50)
    
    # Create window
    cv2.namedWindow("Camera Test - Press Q to quit", cv2.WINDOW_NORMAL)
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("[ERROR] Failed to read frame!")
            break
        
        frame_count += 1
        
        # Add text overlay
        cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press Q to quit", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow("Camera Test - Press Q to quit", frame)
        
        # Check for quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            print(f"\nTest complete! Captured {frame_count} frames.")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return True


if __name__ == "__main__":
    print("\nStarting camera test...")
    success = test_camera()
    
    if success:
        print("\n[SUCCESS] Camera is working correctly!")
        print("You can now run: py -3.12 main.py")
    else:
        print("\n[FAILED] Camera test failed!")
        
    input("\nPress Enter to exit...")
