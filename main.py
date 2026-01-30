"""
Live Face Verification System
Main Application Entry Point
"""
import os
import sys
import cv2
import shutil
from tkinter import Tk, filedialog

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.camera import Camera
from modules.face_detector import FaceDetector
from modules.embeddings import EmbeddingGenerator
from modules.verifier import Verifier
from modules.liveness import LivenessDetector
from database.db_manager import DatabaseManager
from ui.display import Display
from utils.helpers import (
    generate_user_id, save_image, print_menu, 
    get_user_input, clear_console, format_timestamp
)
from config import (
    ENROLLED_IMAGES_DIR, LIVENESS_ENABLED,
    VERIFICATION_FRAMES, VERIFICATION_MAJORITY
)


class FaceVerificationSystem:
    """Main application class for Face Verification System"""
    
    def __init__(self):
        """Initialize all system components"""
        print("Initializing Face Verification System...")
        
        self.camera = Camera()
        self.detector = FaceDetector()
        self.embedding_generator = EmbeddingGenerator()
        self.verifier = Verifier()
        self.liveness = LivenessDetector() if LIVENESS_ENABLED else None
        self.db = DatabaseManager()
        self.display = Display()
        
        print("System initialized successfully!")
    
    def run(self):
        """Run main application loop"""
        while True:
            clear_console()
            self._show_main_menu()
            
            choice = get_user_input("\nEnter choice: ", ['1', '2', '3', '4'])
            
            if choice == '1':
                self.enroll_user()
            elif choice == '2':
                self.live_verification()
            elif choice == '3':
                self.manage_users()
            elif choice == '4':
                print("\nExiting... Goodbye!")
                break
    
    def _show_main_menu(self):
        """Display main menu"""
        stats = self.db.get_statistics()
        
        print("\n" + "=" * 60)
        print("        LIVE FACE VERIFICATION SYSTEM")
        print("=" * 60)
        print(f"  Enrolled Users: {stats['total_users']}")
        print(f"  Total Embeddings: {stats['total_embeddings']}")
        print("=" * 60)
        
        print_menu("Main Menu", [
            ('1', 'Enroll New User'),
            ('2', 'Live Verification'),
            ('3', 'Manage Users'),
            ('4', 'Exit')
        ])
    
    def enroll_user(self):
        """Enroll a new user"""
        clear_console()
        print("\n" + "=" * 60)
        print("        USER ENROLLMENT")
        print("=" * 60)
        
        # Get user details
        user_id = input("\nEnter User ID (or press Enter for auto-generated): ").strip()
        if not user_id:
            user_id = generate_user_id()
            print(f"Generated User ID: {user_id}")
        
        # Check if user exists
        if self.db.user_exists(user_id):
            print(f"Error: User '{user_id}' already exists!")
            input("\nPress Enter to continue...")
            return
        
        name = input("Enter User Name: ").strip()
        if not name:
            print("Error: Name cannot be empty!")
            input("\nPress Enter to continue...")
            return
        
        print(f"\nEnrolling user: {name} ({user_id})")
        
        # Choose enrollment method
        print("\n" + "-" * 40)
        print("Choose enrollment method:")
        print("  [1] Use Webcam (capture live images)")
        print("  [2] Upload Images (from phone/files)")
        print("-" * 40)
        
        method = get_user_input("\nEnter choice (1 or 2): ", ['1', '2'])
        
        # Create user directory
        user_dir = os.path.join(ENROLLED_IMAGES_DIR, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        if method == '2':
            # Upload images from files
            captured_faces, captured_images = self._enroll_from_files(user_dir)
        else:
            # Use webcam
            captured_faces, captured_images = self._enroll_from_camera(user_dir)
        
        # Process captured images
        if not captured_faces:
            print("\nNo valid face images. Enrollment cancelled.")
            # Clean up empty directory
            if os.path.exists(user_dir) and not os.listdir(user_dir):
                os.rmdir(user_dir)
            input("\nPress Enter to continue...")
            return
        
        print(f"\nProcessing {len(captured_faces)} images...")
        
        # Generate embeddings
        embeddings = []
        for i, face_img in enumerate(captured_faces):
            print(f"Generating embedding {i + 1}/{len(captured_faces)}...")
            embedding = self.embedding_generator.generate_embedding(face_img)
            if embedding is not None:
                embeddings.append(embedding)
        
        if not embeddings:
            print("Error: Could not generate any embeddings!")
            input("\nPress Enter to continue...")
            return
        
        # Save to database
        self.db.add_user(user_id, name)
        
        for i, embedding in enumerate(embeddings):
            image_path = captured_images[i] if i < len(captured_images) else None
            self.db.add_embedding(user_id, embedding, image_path)
        
        print(f"\n{'=' * 40}")
        print(f"User enrolled successfully!")
        print(f"  User ID: {user_id}")
        print(f"  Name: {name}")
        print(f"  Embeddings stored: {len(embeddings)}")
        print(f"{'=' * 40}")
        
        input("\nPress Enter to continue...")
    
    def _enroll_from_files(self, user_dir):
        """Enroll user using image files"""
        print("\n" + "-" * 40)
        print("IMAGE UPLOAD INSTRUCTIONS:")
        print("-" * 40)
        print("1. A file dialog will open")
        print("2. Select 3-5 clear photos of your face")
        print("3. Photos can be from your phone, camera, etc.")
        print("4. Make sure your face is clearly visible")
        print("-" * 40)
        input("\nPress Enter to open file dialog...")
        
        # Use tkinter file dialog
        root = Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring dialog to front
        
        file_paths = filedialog.askopenfilenames(
            title="Select Face Images (3-5 photos)",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        root.destroy()
        
        if not file_paths:
            print("No files selected!")
            return [], []
        
        print(f"\nSelected {len(file_paths)} files. Processing...")
        
        captured_faces = []
        captured_images = []
        
        for i, file_path in enumerate(file_paths):
            print(f"\nProcessing image {i + 1}: {os.path.basename(file_path)}")
            
            # Read image
            img = cv2.imread(file_path)
            if img is None:
                print(f"  Error: Could not read image")
                continue
            
            # Detect faces
            faces = self.detector.detect_faces(img)
            
            if not faces:
                print(f"  Warning: No face detected in this image")
                continue
            
            # Get largest face
            face = self.detector.get_largest_face(faces)
            
            # Copy image to user directory
            new_filename = f"img_{len(captured_images) + 1}{os.path.splitext(file_path)[1]}"
            new_path = os.path.join(user_dir, new_filename)
            shutil.copy2(file_path, new_path)
            
            captured_faces.append(face['face_img'])
            captured_images.append(new_path)
            print(f"  Success: Face detected and saved")
        
        print(f"\nTotal valid images: {len(captured_faces)}")
        return captured_faces, captured_images
    
    def _enroll_from_camera(self, user_dir):
        """Enroll user using webcam"""
        print("\n" + "-" * 40)
        print("WEBCAM INSTRUCTIONS:")
        print("-" * 40)
        print("1. Position your face in the camera frame")
        print("2. Press SPACE to capture images (capture 3-5)")
        print("3. Try different angles and expressions")
        print("4. Press Q when done capturing")
        print("-" * 40)
        input("\nPress Enter to start camera...")
        
        captured_images = []
        captured_faces = []
        
        try:
            self.camera.start()
            
            while True:
                ret, frame = self.camera.read_frame()
                if not ret:
                    print("Error: Could not read from camera")
                    break
                
                # Detect faces
                faces = self.detector.detect_faces(frame)
                
                # Draw faces
                for face in faces:
                    x, y, w, h = face['box']
                    quality = self.detector.check_quality(face['face_img'])
                    
                    if quality['passed']:
                        self.display.draw_face_box(frame, (x, y, w, h), 'verified', 'Good Quality')
                    else:
                        self.display.draw_face_box(frame, (x, y, w, h), 'detecting', quality['reason'])
                
                # Draw enrollment progress
                self.display.draw_enrollment_progress(frame, len(captured_images), 5)
                self.display.draw_fps(frame, self.camera.get_fps())
                
                self.display.show(frame)
                
                key = self.display.wait_key(1)
                
                if key == ord('q') or key == ord('Q'):
                    break
                    
                elif key == ord(' '):  # Space key
                    if faces:
                        face = self.detector.get_largest_face(faces)
                        # Save image (no quality check - accept all)
                        img_path = save_image(frame, user_dir, f"img_{len(captured_images) + 1}.jpg")
                        captured_images.append(img_path)
                        captured_faces.append(face['face_img'])
                        print(f"Captured image {len(captured_images)}")
                    else:
                        print("No face detected!")
            
            self.camera.stop()
            self.display.close()
            
        except Exception as e:
            print(f"Error during capture: {e}")
            self.camera.stop()
            self.display.close()
        
        return captured_faces, captured_images
    
    def live_verification(self):
        """Run live face verification"""
        clear_console()
        print("\n" + "=" * 60)
        print("        FACE VERIFICATION")
        print("=" * 60)
        
        # Check if users exist
        users = self.db.get_all_users()
        if not users:
            print("\nNo users enrolled! Please enroll a user first.")
            input("\nPress Enter to continue...")
            return
        
        print(f"\nEnrolled users: {len(users)}")
        for user in users:
            count = self.db.get_embedding_count(user['user_id'])
            print(f"  - {user['name']} ({user['user_id']}) - {count} embeddings")
        
        # Choose verification method
        print("\n" + "-" * 40)
        print("Choose verification method:")
        print("  [1] Use Webcam (live verification)")
        print("  [2] Upload Image (from phone/file)")
        print("-" * 40)
        
        method = get_user_input("\nEnter choice (1 or 2): ", ['1', '2'])
        
        if method == '2':
            self._verify_from_image()
        else:
            self._verify_from_camera()
        
        input("\nPress Enter to continue...")
    
    def _verify_from_image(self):
        """Verify using uploaded image"""
        print("\n" + "-" * 40)
        print("Select an image to verify...")
        print("-" * 40)
        
        # Use tkinter file dialog
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title="Select Image to Verify",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        root.destroy()
        
        if not file_path:
            print("No file selected!")
            return
        
        print(f"\nProcessing: {os.path.basename(file_path)}")
        
        # Read image
        img = cv2.imread(file_path)
        if img is None:
            print("Error: Could not read image!")
            return
        
        # Detect face
        faces = self.detector.detect_faces(img)
        
        if not faces:
            print("Error: No face detected in the image!")
            return
        
        face = self.detector.get_largest_face(faces)
        print("Face detected! Generating embedding...")
        
        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(face['face_img'])
        
        if embedding is None:
            print("Error: Could not generate embedding!")
            return
        
        # Verify against database
        result = self.verifier.verify_with_database(embedding, self.db)
        
        # Display result
        print("\n" + "=" * 40)
        if result['verified']:
            print(f"  ✓ VERIFIED")
            print(f"  User: {result['user_name']}")
            print(f"  Confidence: {result['confidence']:.1f}%")
        else:
            print(f"  ✗ NOT VERIFIED")
            print(f"  Confidence: {result['confidence']:.1f}%")
        print("=" * 40)
        
        # Show image with result
        x, y, w, h = face['box']
        color = (0, 255, 0) if result['verified'] else (0, 0, 255)
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)
        
        label = f"{result.get('user_name', 'Unknown')} ({result['confidence']:.1f}%)" if result['verified'] else "Not Verified"
        cv2.putText(img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        
        # Resize for display if too large
        max_dim = 800
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        
        cv2.imshow("Verification Result - Press any key to close", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def _verify_from_camera(self):
        
        print("\n" + "-" * 40)
        print("Instructions:")
        print("  1. Position your face in the camera frame")
        print("  2. System will automatically verify your identity")
        print("  3. Green box = Verified, Red box = Not Verified")
        if LIVENESS_ENABLED:
            print("  4. Blink to confirm liveness")
        print("  5. Press Q to exit")
        print("-" * 40)
        input("\nPress Enter to start verification...")
        
        # Reset verifier
        self.verifier.reset_voting()
        if self.liveness:
            self.liveness.reset()
        
        try:
            self.camera.start()
            
            while True:
                ret, frame = self.camera.read_frame()
                if not ret:
                    print("Error: Could not read from camera")
                    break
                
                # Detect faces
                faces = self.detector.detect_faces(frame)
                
                if faces:
                    face = self.detector.get_largest_face(faces)
                    x, y, w, h = face['box']
                    
                    # Generate embedding (skip quality check)
                    embedding = self.embedding_generator.generate_embedding(face['face_img'])
                    
                    if embedding is not None:
                        # Verify against database
                        result = self.verifier.verify_with_database(embedding, self.db)
                        
                        # Apply voting
                        result = self.verifier.verify_with_voting(result)
                        
                        # Draw result
                        if result['verified']:
                            self.display.draw_face_box(
                                frame, (x, y, w, h), 'verified',
                                result.get('user_name', 'Unknown'),
                                result['confidence']
                            )
                            self.display.draw_verification_result(
                                frame, result, result.get('user_name')
                            )
                        else:
                            self.display.draw_face_box(
                                frame, (x, y, w, h), 'not_verified',
                                'Not Verified',
                                result['confidence']
                            )
                            self.display.draw_verification_result(frame, result)
                else:
                    self.display.draw_status(frame, "No face detected", 'top', (0, 255, 255))
                    self.verifier.reset_voting()
                
                # Draw FPS
                self.display.draw_fps(frame, self.camera.get_fps())
                
                self.display.show(frame)
                
                key = self.display.wait_key(1)
                if key == ord('q') or key == ord('Q') or key == 27:  # Q or ESC
                    break
            
            self.camera.stop()
            self.display.close()
            
        except Exception as e:
            print(f"Error during verification: {e}")
            self.camera.stop()
            self.display.close()
    
    def manage_users(self):
        """Manage enrolled users"""
        while True:
            clear_console()
            print("\n" + "=" * 60)
            print("        MANAGE USERS")
            print("=" * 60)
            
            users = self.db.get_all_users()
            
            if not users:
                print("\nNo users enrolled.")
            else:
                print(f"\nEnrolled Users ({len(users)}):")
                print("-" * 40)
                for i, user in enumerate(users, 1):
                    count = self.db.get_embedding_count(user['user_id'])
                    print(f"  {i}. {user['name']}")
                    print(f"     ID: {user['user_id']}")
                    print(f"     Embeddings: {count}")
                    print(f"     Created: {user['created_at']}")
                    print()
            
            print_menu("Options", [
                ('D', 'Delete a user'),
                ('B', 'Back to main menu')
            ])
            
            choice = get_user_input("\nEnter choice: ", ['d', 'D', 'b', 'B'])
            
            if choice.lower() == 'b':
                break
            elif choice.lower() == 'd':
                if not users:
                    print("\nNo users to delete!")
                    input("\nPress Enter to continue...")
                    continue
                
                user_id = input("\nEnter User ID to delete: ").strip()
                
                if not self.db.user_exists(user_id):
                    print(f"User '{user_id}' not found!")
                    input("\nPress Enter to continue...")
                    continue
                
                confirm = input(f"Are you sure you want to delete '{user_id}'? (yes/no): ").strip().lower()
                
                if confirm == 'yes':
                    # Delete user directory
                    user_dir = os.path.join(ENROLLED_IMAGES_DIR, user_id)
                    if os.path.exists(user_dir):
                        shutil.rmtree(user_dir)
                    
                    # Delete from database
                    self.db.delete_user(user_id)
                    print(f"\nUser '{user_id}' deleted successfully!")
                else:
                    print("\nDeletion cancelled.")
                
                input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    try:
        system = FaceVerificationSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
