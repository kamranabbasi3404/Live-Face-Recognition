"""
Database Manager Module - Handles SQLite database operations for face embeddings
"""
import sqlite3
import numpy as np
import os
from datetime import datetime
from config import DATABASE_PATH


class DatabaseManager:
    """Manages SQLite database for storing user data and embeddings"""
    
    def __init__(self, db_path=DATABASE_PATH):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_exists()
        self._create_tables()
    
    def _ensure_db_exists(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Embeddings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                embedding BLOB NOT NULL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, name):
        """
        Add a new user
        
        Args:
            user_id: Unique user identifier
            name: User's name
            
        Returns:
            bool: True if successful, False if user already exists
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO users (user_id, name) VALUES (?, ?)',
                (user_id, name)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, user_id):
        """
        Get user by ID
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: User data or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT user_id, name, created_at FROM users WHERE user_id = ?',
            (user_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'name': row[1],
                'created_at': row[2]
            }
        return None
    
    def get_all_users(self):
        """
        Get all users
        
        Returns:
            list: List of user dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, name, created_at FROM users ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {'user_id': row[0], 'name': row[1], 'created_at': row[2]}
            for row in rows
        ]
    
    def delete_user(self, user_id):
        """
        Delete a user and their embeddings
        
        Args:
            user_id: User identifier
            
        Returns:
            bool: True if user was deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Delete embeddings first
        cursor.execute('DELETE FROM embeddings WHERE user_id = ?', (user_id,))
        
        # Delete user
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def add_embedding(self, user_id, embedding, image_path=None):
        """
        Add an embedding for a user
        
        Args:
            user_id: User identifier
            embedding: Numpy array embedding vector
            image_path: Optional path to source image
            
        Returns:
            int: Embedding ID or None if failed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Convert embedding to bytes
            embedding_bytes = embedding.tobytes()
            
            cursor.execute(
                'INSERT INTO embeddings (user_id, embedding, image_path) VALUES (?, ?, ?)',
                (user_id, embedding_bytes, image_path)
            )
            
            embedding_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return embedding_id
            
        except Exception as e:
            print(f"Error adding embedding: {e}")
            return None
    
    def get_embeddings(self, user_id):
        """
        Get all embeddings for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            list: List of numpy array embeddings
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT embedding FROM embeddings WHERE user_id = ?',
            (user_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        embeddings = []
        for row in rows:
            # Convert bytes back to numpy array
            embedding = np.frombuffer(row[0], dtype=np.float64)
            embeddings.append(embedding)
        
        return embeddings
    
    def get_embedding_count(self, user_id):
        """
        Get number of embeddings for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Number of embeddings
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT COUNT(*) FROM embeddings WHERE user_id = ?',
            (user_id,)
        )
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def user_exists(self, user_id):
        """
        Check if user exists
        
        Args:
            user_id: User identifier
            
        Returns:
            bool: True if user exists
        """
        return self.get_user(user_id) is not None
    
    def get_statistics(self):
        """
        Get database statistics
        
        Returns:
            dict: Statistics about users and embeddings
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        embedding_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': user_count,
            'total_embeddings': embedding_count,
            'avg_embeddings_per_user': embedding_count / user_count if user_count > 0 else 0
        }


def test_database():
    """Test database operations"""
    import tempfile
    
    # Use temporary database for testing
    test_db = os.path.join(tempfile.gettempdir(), 'test_face_db.sqlite')
    
    db = DatabaseManager(test_db)
    
    print("Testing database operations...")
    
    # Test add user
    result = db.add_user('user1', 'John Doe')
    print(f"Add user: {'Success' if result else 'Failed'}")
    
    # Test get user
    user = db.get_user('user1')
    print(f"Get user: {user}")
    
    # Test add embedding
    test_embedding = np.random.randn(512).astype(np.float64)
    emb_id = db.add_embedding('user1', test_embedding)
    print(f"Add embedding ID: {emb_id}")
    
    # Test get embeddings
    embeddings = db.get_embeddings('user1')
    print(f"Embeddings count: {len(embeddings)}")
    print(f"Embedding shape: {embeddings[0].shape if embeddings else 'N/A'}")
    
    # Test statistics
    stats = db.get_statistics()
    print(f"Statistics: {stats}")
    
    # Test delete user
    deleted = db.delete_user('user1')
    print(f"Delete user: {'Success' if deleted else 'Failed'}")
    
    # Cleanup
    os.remove(test_db)
    print("\nDatabase test complete!")


if __name__ == "__main__":
    test_database()
