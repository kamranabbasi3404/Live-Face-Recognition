"""
Live Face Recognition - Streamlit Web App
Deploy on Hugging Face Spaces or Streamlit Cloud
"""
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import tempfile
import os
import sqlite3
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Live Face Recognition",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #C8E6C9;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
    }
    .error-box {
        padding: 1rem;
        background-color: #FFCDD2;
        border-radius: 10px;
        border-left: 5px solid #F44336;
    }
    .info-box {
        padding: 1rem;
        background-color: #BBDEFB;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'detector' not in st.session_state:
    st.session_state.detector = None
if 'embedding_generator' not in st.session_state:
    st.session_state.embedding_generator = None
if 'verifier' not in st.session_state:
    st.session_state.verifier = None


@st.cache_resource
def load_models():
    """Load face detection and embedding models"""
    try:
        from modules.face_detector import FaceDetector
        from modules.embeddings import EmbeddingGenerator
        from modules.verifier import Verifier
        
        detector = FaceDetector()
        embedding_gen = EmbeddingGenerator()
        verifier = Verifier()
        
        return detector, embedding_gen, verifier
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None, None


class SimpleDBManager:
    """Simple SQLite database manager for web app"""
    
    def __init__(self, db_path="web_face_db.sqlite"):
        self.db_path = db_path
        self._create_tables()
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def _create_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, name):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (user_id, name) VALUES (?, ?)', (user_id, name))
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_all_users(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name, created_at FROM users ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [{'user_id': row[0], 'name': row[1], 'created_at': row[2]} for row in rows]
    
    def delete_user(self, user_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM embeddings WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def add_embedding(self, user_id, embedding):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            embedding_bytes = embedding.tobytes()
            cursor.execute('INSERT INTO embeddings (user_id, embedding) VALUES (?, ?)', 
                         (user_id, embedding_bytes))
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_embeddings(self, user_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT embedding FROM embeddings WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [np.frombuffer(row[0], dtype=np.float64) for row in rows]
    
    def user_exists(self, user_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists


def main():
    # Header
    st.markdown('<h1 class="main-header">👤 Live Face Recognition</h1>', unsafe_allow_html=True)
    
    # Initialize database
    db = SimpleDBManager()
    
    # Sidebar
    st.sidebar.title("🎯 Navigation")
    page = st.sidebar.radio("Select Page", ["🏠 Home", "➕ Enroll User", "✓ Verify Face", "👥 Manage Users"])
    
    # Load models
    with st.spinner("Loading AI models... (first time takes ~1 min)"):
        detector, embedding_gen, verifier = load_models()
    
    if detector is None:
        st.error("Failed to load models. Please check installation.")
        return
    
    if page == "🏠 Home":
        show_home_page()
    elif page == "➕ Enroll User":
        show_enroll_page(db, detector, embedding_gen, verifier)
    elif page == "✓ Verify Face":
        show_verify_page(db, detector, embedding_gen, verifier)
    elif page == "👥 Manage Users":
        show_users_page(db)


def show_home_page():
    """Show home page"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="info-box">
            <h3>➕ Enroll User</h3>
            <p>Register a new face in the system by capturing photos from your webcam.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-box">
            <h3>✓ Verify Face</h3>
            <p>Verify if a person is registered by comparing their face with the database.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="info-box">
            <h3>👥 Manage Users</h3>
            <p>View, search, and delete registered users from the system.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.info("👈 Use the sidebar to navigate between pages")


def show_enroll_page(db, detector, embedding_gen, verifier):
    """Show enrollment page"""
    st.header("➕ Enroll New User")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # User input fields
        user_name = st.text_input("Full Name *", placeholder="Enter full name")
        user_id = st.text_input("User ID (optional)", placeholder="Leave empty for auto-generate")
        
        if not user_id and user_name:
            user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.caption(f"Auto-generated ID: {user_id}")
    
    with col2:
        st.subheader("📷 Capture Photo")
        
        # Camera input
        img_file = st.camera_input("Take a photo for enrollment")
        
        if img_file is not None:
            # Convert to numpy array
            img = Image.open(img_file)
            img_array = np.array(img)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Detect face
            faces = detector.detect_faces(img_bgr)
            
            if faces:
                face = detector.get_largest_face(faces)
                
                # Check for duplicate
                embedding = embedding_gen.generate_embedding(face['face_img'])
                
                if embedding is not None:
                    result = verifier.verify_with_database(embedding, db)
                    
                    if result['distance'] < 0.20:  # Duplicate threshold
                        st.error(f"❌ This face is already registered as: {result['user_name']}")
                    else:
                        st.success("✅ Face detected! Ready to enroll.")
                        
                        if st.button("💾 Save User", type="primary"):
                            if not user_name:
                                st.error("Please enter a name!")
                            else:
                                # Save user
                                if db.add_user(user_id, user_name):
                                    db.add_embedding(user_id, embedding)
                                    st.balloons()
                                    st.success(f"✅ User '{user_name}' enrolled successfully!")
                                else:
                                    st.error("Failed to save user. ID may already exist.")
            else:
                st.warning("⚠️ No face detected. Please take another photo.")


def show_verify_page(db, detector, embedding_gen, verifier):
    """Show verification page"""
    st.header("✓ Face Verification")
    
    users = db.get_all_users()
    if not users:
        st.warning("⚠️ No users enrolled yet! Please enroll a user first.")
        return
    
    st.info(f"📊 {len(users)} users in database")
    
    # Camera input
    img_file = st.camera_input("Take a photo to verify")
    
    if img_file is not None:
        # Convert to numpy array
        img = Image.open(img_file)
        img_array = np.array(img)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        with st.spinner("🔍 Analyzing face..."):
            # Detect face
            faces = detector.detect_faces(img_bgr)
            
            if faces:
                face = detector.get_largest_face(faces)
                
                # Generate embedding
                embedding = embedding_gen.generate_embedding(face['face_img'])
                
                if embedding is not None:
                    # Verify against database
                    result = verifier.verify_with_database(embedding, db)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Draw box on face
                        x, y, w, h = face['box']
                        color = (0, 255, 0) if result['verified'] else (255, 0, 0)
                        cv2.rectangle(img_bgr, (x, y), (x+w, y+h), color, 3)
                        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                        st.image(img_rgb, caption="Detected Face")
                    
                    with col2:
                        if result['verified']:
                            st.markdown(f"""
                            <div class="success-box">
                                <h2>✅ ACCESS GRANTED</h2>
                                <h3>Welcome, {result['user_name']}!</h3>
                                <p>Confidence: {result['confidence']:.1f}%</p>
                                <p>Distance: {result['distance']:.4f}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.balloons()
                        else:
                            st.markdown(f"""
                            <div class="error-box">
                                <h2>❌ ACCESS DENIED</h2>
                                <p>Face not recognized in database.</p>
                                <p>Closest match: {result['user_name'] or 'None'}</p>
                                <p>Distance: {result['distance']:.4f}</p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error("Failed to generate face embedding.")
            else:
                st.warning("⚠️ No face detected. Please take another photo.")


def show_users_page(db):
    """Show user management page"""
    st.header("👥 Manage Users")
    
    users = db.get_all_users()
    
    if not users:
        st.info("No users enrolled yet.")
        return
    
    st.info(f"📊 Total users: {len(users)}")
    
    # Search
    search = st.text_input("🔍 Search users", placeholder="Enter name or ID")
    
    # Filter users
    if search:
        users = [u for u in users if search.lower() in u['name'].lower() or search.lower() in u['user_id'].lower()]
    
    # Display users in a table
    for user in users:
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.write(f"**{user['name']}**")
            st.caption(f"ID: {user['user_id']}")
        
        with col2:
            st.caption(f"Enrolled: {user['created_at']}")
        
        with col3:
            if st.button("🗑️ Delete", key=f"del_{user['user_id']}"):
                if db.delete_user(user['user_id']):
                    st.success(f"Deleted {user['name']}")
                    st.rerun()
        
        st.markdown("---")


if __name__ == "__main__":
    main()
