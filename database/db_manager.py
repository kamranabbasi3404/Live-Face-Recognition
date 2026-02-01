"""
Database Manager Module - Handles SQLite database operations for face embeddings
With Multi-User Authentication Support
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
        self._migrate_tables()
    
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
        
        # Accounts table (for user authentication)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Users table (enrolled faces)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES accounts(id) ON DELETE CASCADE
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
    
    def _migrate_tables(self):
        """Add owner_id column if it doesn't exist (for existing databases)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if owner_id column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'owner_id' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN owner_id INTEGER REFERENCES accounts(id)')
            conn.commit()
        
        conn.close()
    
    # ==================== ACCOUNT METHODS ====================
    
    def create_account(self, email, password_hash, name):
        """
        Create a new account
        
        Args:
            email: User email (unique)
            password_hash: Hashed password
            name: User's display name
            
        Returns:
            int: Account ID or None if failed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO accounts (email, password_hash, name) VALUES (?, ?, ?)',
                (email, password_hash, name)
            )
            
            account_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return account_id
            
        except sqlite3.IntegrityError:
            return None
    
    def get_account_by_email(self, email):
        """
        Get account by email
        
        Args:
            email: Account email
            
        Returns:
            dict: Account data or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, email, password_hash, name, created_at FROM accounts WHERE email = ?',
            (email,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'password_hash': row[2],
                'name': row[3],
                'created_at': row[4]
            }
        return None
    
    def get_account_by_id(self, account_id):
        """
        Get account by ID
        
        Args:
            account_id: Account ID
            
        Returns:
            dict: Account data or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, email, name, created_at FROM accounts WHERE id = ?',
            (account_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'created_at': row[3]
            }
        return None
    
    # ==================== USER METHODS (with owner filtering) ====================
    
    def add_user(self, user_id, name, owner_id=None):
        """
        Add a new user (enrolled face)
        
        Args:
            user_id: Unique user identifier
            name: User's name
            owner_id: Account ID of the owner
            
        Returns:
            bool: True if successful, False if user already exists
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO users (user_id, name, owner_id) VALUES (?, ?, ?)',
                (user_id, name, owner_id)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, user_id, owner_id=None):
        """
        Get user by ID (optionally filtered by owner)
        
        Args:
            user_id: User identifier
            owner_id: Optional owner account ID
            
        Returns:
            dict: User data or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if owner_id is not None:
            cursor.execute(
                'SELECT user_id, name, owner_id, created_at FROM users WHERE user_id = ? AND owner_id = ?',
                (user_id, owner_id)
            )
        else:
            cursor.execute(
                'SELECT user_id, name, owner_id, created_at FROM users WHERE user_id = ?',
                (user_id,)
            )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'name': row[1],
                'owner_id': row[2],
                'created_at': row[3]
            }
        return None
    
    def get_all_users(self, owner_id=None):
        """
        Get all users (filtered by owner if specified)
        
        Args:
            owner_id: Account ID to filter by (None = all users)
            
        Returns:
            list: List of user dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if owner_id is not None:
            cursor.execute(
                'SELECT user_id, name, owner_id, created_at FROM users WHERE owner_id = ? ORDER BY created_at DESC',
                (owner_id,)
            )
        else:
            cursor.execute('SELECT user_id, name, owner_id, created_at FROM users ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {'user_id': row[0], 'name': row[1], 'owner_id': row[2], 'created_at': row[3]}
            for row in rows
        ]
    
    def delete_user(self, user_id, owner_id=None):
        """
        Delete a user and their embeddings (optionally verify owner)
        
        Args:
            user_id: User identifier
            owner_id: Optional owner ID (if set, only delete if owned by this account)
            
        Returns:
            bool: True if user was deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Verify ownership if owner_id provided
        if owner_id is not None:
            cursor.execute('SELECT owner_id FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if not row or row[0] != owner_id:
                conn.close()
                return False
        
        # Delete embeddings first
        cursor.execute('DELETE FROM embeddings WHERE user_id = ?', (user_id,))
        
        # Delete user (with owner check if specified)
        if owner_id is not None:
            cursor.execute('DELETE FROM users WHERE user_id = ? AND owner_id = ?', (user_id, owner_id))
        else:
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
    
    def get_all_embeddings_with_users(self, owner_id=None):
        """
        Get all embeddings with user info (filtered by owner)
        
        Args:
            owner_id: Account ID to filter by
            
        Returns:
            list: List of (user_id, name, embedding) tuples
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if owner_id is not None:
            cursor.execute('''
                SELECT u.user_id, u.name, e.embedding 
                FROM users u 
                JOIN embeddings e ON u.user_id = e.user_id 
                WHERE u.owner_id = ?
            ''', (owner_id,))
        else:
            cursor.execute('''
                SELECT u.user_id, u.name, e.embedding 
                FROM users u 
                JOIN embeddings e ON u.user_id = e.user_id
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            embedding = np.frombuffer(row[2], dtype=np.float64)
            result.append({
                'user_id': row[0],
                'name': row[1],
                'embedding': embedding
            })
        
        return result
    
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
    
    def get_statistics(self, owner_id=None):
        """
        Get database statistics (filtered by owner if specified)
        
        Args:
            owner_id: Account ID to filter by
            
        Returns:
            dict: Statistics about users and embeddings
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if owner_id is not None:
            cursor.execute('SELECT COUNT(*) FROM users WHERE owner_id = ?', (owner_id,))
            user_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM embeddings e 
                JOIN users u ON e.user_id = u.user_id 
                WHERE u.owner_id = ?
            ''', (owner_id,))
            embedding_count = cursor.fetchone()[0]
        else:
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
    
    # Test create account
    account_id = db.create_account('test@example.com', 'hashed_password', 'Test User')
    print(f"Create account ID: {account_id}")
    
    # Test get account
    account = db.get_account_by_email('test@example.com')
    print(f"Get account: {account}")
    
    # Test add user with owner
    result = db.add_user('user1', 'John Doe', owner_id=account_id)
    print(f"Add user: {'Success' if result else 'Failed'}")
    
    # Test get user
    user = db.get_user('user1', owner_id=account_id)
    print(f"Get user: {user}")
    
    # Test add embedding
    test_embedding = np.random.randn(512).astype(np.float64)
    emb_id = db.add_embedding('user1', test_embedding)
    print(f"Add embedding ID: {emb_id}")
    
    # Test get all users filtered by owner
    users = db.get_all_users(owner_id=account_id)
    print(f"Users for account: {len(users)}")
    
    # Test get all embeddings with users
    emb_data = db.get_all_embeddings_with_users(owner_id=account_id)
    print(f"Embeddings with users: {len(emb_data)}")
    
    # Test statistics
    stats = db.get_statistics(owner_id=account_id)
    print(f"Statistics: {stats}")
    
    # Test delete user
    deleted = db.delete_user('user1', owner_id=account_id)
    print(f"Delete user: {'Success' if deleted else 'Failed'}")
    
    # Cleanup
    os.remove(test_db)
    print("\nDatabase test complete!")


if __name__ == "__main__":
    test_database()
