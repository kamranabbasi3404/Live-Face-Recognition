"""
Embeddings Module - Generates face embeddings using DeepFace
"""
import numpy as np
from config import EMBEDDING_MODEL


class EmbeddingGenerator:
    """Generates face embeddings using DeepFace"""
    
    def __init__(self, model_name=EMBEDDING_MODEL):
        """
        Initialize embedding generator
        
        Args:
            model_name: Model to use (VGG-Face, Facenet, Facenet512, etc.)
        """
        self.model_name = model_name
        self._model = None
        self._deepface = None
    
    def _load_model(self):
        """Lazy load the DeepFace model"""
        if self._deepface is None:
            from deepface import DeepFace
            self._deepface = DeepFace
            # Pre-load model by running a dummy embedding
            print(f"Loading {self.model_name} model (first time may take a moment)...")
    
    def generate_embedding(self, face_img):
        """
        Generate embedding for a face image
        
        Args:
            face_img: Face image (numpy array, BGR)
            
        Returns:
            numpy array: Embedding vector or None if failed
        """
        if face_img is None or face_img.size == 0:
            return None
        
        try:
            self._load_model()
            
            # Generate embedding using DeepFace
            result = self._deepface.represent(
                img_path=face_img,
                model_name=self.model_name,
                enforce_detection=False,
                detector_backend='skip'  # Face already detected
            )
            
            if result and len(result) > 0:
                embedding = np.array(result[0]['embedding'])
                # Normalize embedding
                embedding = embedding / np.linalg.norm(embedding)
                return embedding
            
            return None
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, face_images):
        """
        Generate embeddings for multiple face images
        
        Args:
            face_images: List of face images
            
        Returns:
            list: List of embedding vectors
        """
        embeddings = []
        for img in face_images:
            emb = self.generate_embedding(img)
            if emb is not None:
                embeddings.append(emb)
        return embeddings
    
    def get_embedding_size(self):
        """Get the size of embedding vector for the current model"""
        model_sizes = {
            'VGG-Face': 4096,
            'Facenet': 128,
            'Facenet512': 512,
            'OpenFace': 128,
            'DeepFace': 4096,
            'DeepID': 160,
            'ArcFace': 512,
            'Dlib': 128,
            'SFace': 128
        }
        return model_sizes.get(self.model_name, 512)


def test_embedding_generator():
    """Test embedding generator with webcam"""
    import cv2
    from camera import Camera
    from face_detector import FaceDetector
    
    generator = EmbeddingGenerator()
    detector = FaceDetector()
    
    with Camera() as cam:
        print("Embedding test - Press 'c' to capture and generate embedding, 'q' to quit")
        
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                break
            
            faces = detector.detect_faces(frame)
            
            for face in faces:
                x, y, w, h = face['box']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            cv2.imshow("Embedding Test", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c') and faces:
                face = detector.get_largest_face(faces)
                print("Generating embedding...")
                embedding = generator.generate_embedding(face['face_img'])
                if embedding is not None:
                    print(f"Embedding shape: {embedding.shape}")
                    print(f"Embedding norm: {np.linalg.norm(embedding):.4f}")
                    print(f"First 5 values: {embedding[:5]}")
                else:
                    print("Failed to generate embedding")
        
        cv2.destroyAllWindows()


if __name__ == "__main__":
    test_embedding_generator()
