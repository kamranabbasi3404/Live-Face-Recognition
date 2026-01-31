"""
Verifier Module - Compares embeddings and makes verification decisions
"""
import numpy as np
from collections import deque
from config import (
    VERIFICATION_THRESHOLD, DISTANCE_METRIC,
    VERIFICATION_FRAMES, VERIFICATION_MAJORITY
)


class Verifier:
    """Handles face verification by comparing embeddings"""
    
    def __init__(self, threshold=VERIFICATION_THRESHOLD, metric=DISTANCE_METRIC):
        """
        Initialize verifier
        
        Args:
            threshold: Distance threshold for verification
            metric: Distance metric (cosine, euclidean, euclidean_l2)
        """
        self.threshold = threshold
        self.metric = metric
        self.verification_history = deque(maxlen=VERIFICATION_FRAMES)
    
    def calculate_distance(self, embedding1, embedding2):
        """
        Calculate distance between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            float: Distance value
        """
        if embedding1 is None or embedding2 is None:
            return float('inf')
        
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)
        
        if self.metric == 'cosine':
            # Cosine distance
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            similarity = dot_product / (norm1 * norm2 + 1e-10)
            distance = 1 - similarity
            
        elif self.metric == 'euclidean':
            # Euclidean distance
            distance = np.linalg.norm(embedding1 - embedding2)
            
        elif self.metric == 'euclidean_l2':
            # L2 normalized euclidean distance
            embedding1 = embedding1 / (np.linalg.norm(embedding1) + 1e-10)
            embedding2 = embedding2 / (np.linalg.norm(embedding2) + 1e-10)
            distance = np.linalg.norm(embedding1 - embedding2)
            
        else:
            raise ValueError(f"Unknown metric: {self.metric}")
        
        return distance
    
    def verify(self, query_embedding, stored_embeddings):
        """
        Verify if query embedding matches any stored embeddings
        
        Args:
            query_embedding: Embedding to verify
            stored_embeddings: List of stored embeddings for a user
            
        Returns:
            dict: Verification result with distance, confidence, and match status
        """
        if query_embedding is None or not stored_embeddings:
            return {
                'verified': False,
                'distance': float('inf'),
                'confidence': 0.0,
                'user_id': None
            }
        
        # Calculate distance to each stored embedding
        distances = []
        for stored_emb in stored_embeddings:
            dist = self.calculate_distance(query_embedding, stored_emb)
            distances.append(dist)
        
        # Use minimum distance
        min_distance = min(distances)
        
        # Convert distance to confidence (0-100%)
        if self.metric == 'cosine':
            # Cosine distance is 0-2, threshold typically around 0.4
            confidence = max(0, (1 - min_distance / self.threshold) * 100)
        else:
            # Normalize euclidean distance to confidence
            confidence = max(0, (1 - min_distance / (self.threshold * 2)) * 100)
        
        confidence = min(100, confidence)
        
        # Determine verification result
        verified = min_distance < self.threshold
        
        return {
            'verified': verified,
            'distance': min_distance,
            'confidence': confidence
        }
    
    def verify_with_database(self, query_embedding, db_manager):
        """
        Verify against all users in database
        
        Args:
            query_embedding: Embedding to verify
            db_manager: Database manager instance
            
        Returns:
            dict: Verification result including matched user_id if verified
        """
        users = db_manager.get_all_users()
        
        best_match = {
            'verified': False,
            'distance': float('inf'),
            'confidence': 0.0,
            'user_id': None,
            'user_name': None
        }
        
        print(f"\n=== VERIFICATION DEBUG ===")
        print(f"Checking against {len(users)} users, threshold: {self.threshold}")
        
        for user in users:
            user_id = user['user_id']
            embeddings = db_manager.get_embeddings(user_id)
            
            if not embeddings:
                continue
            
            result = self.verify(query_embedding, embeddings)
            
            print(f"  User: {user['name']} | Distance: {result['distance']:.4f} | Verified: {result['verified']}")
            
            if result['distance'] < best_match['distance']:
                best_match = {
                    'verified': result['verified'],
                    'distance': result['distance'],
                    'confidence': result['confidence'],
                    'user_id': user_id,
                    'user_name': user['name']
                }
        
        print(f"  BEST MATCH: {best_match['user_name']} | Distance: {best_match['distance']:.4f}")
        print(f"=========================\n")
        
        return best_match
    
    def verify_with_voting(self, result):
        """
        Apply majority voting to verification results
        
        Args:
            result: Current verification result (dict with 'verified' key)
            
        Returns:
            dict: Updated result with voting applied
        """
        self.verification_history.append(result.copy())
        
        if len(self.verification_history) < VERIFICATION_MAJORITY:
            # Not enough samples yet
            result['voting_status'] = 'collecting'
            result['votes'] = len(self.verification_history)
            result['votes_needed'] = VERIFICATION_MAJORITY
            return result
        
        # Count votes
        verified_votes = sum(1 for r in self.verification_history if r.get('verified', False))
        
        # Apply majority voting
        final_verified = verified_votes >= VERIFICATION_MAJORITY
        
        # Update result
        result['verified'] = final_verified
        result['voting_status'] = 'complete'
        result['votes_verified'] = verified_votes
        result['votes_total'] = len(self.verification_history)
        
        return result
    
    def reset_voting(self):
        """Reset voting history"""
        self.verification_history.clear()
    
    def get_confidence_label(self, confidence):
        """
        Get human-readable confidence label
        
        Args:
            confidence: Confidence percentage (0-100)
            
        Returns:
            str: Confidence label
        """
        if confidence >= 90:
            return "Very High"
        elif confidence >= 75:
            return "High"
        elif confidence >= 60:
            return "Medium"
        elif confidence >= 40:
            return "Low"
        else:
            return "Very Low"


def test_verifier():
    """Test verifier with random embeddings"""
    verifier = Verifier()
    
    # Create test embeddings
    np.random.seed(42)
    base_embedding = np.random.randn(512)
    base_embedding = base_embedding / np.linalg.norm(base_embedding)
    
    # Similar embedding (small perturbation)
    similar_embedding = base_embedding + np.random.randn(512) * 0.1
    similar_embedding = similar_embedding / np.linalg.norm(similar_embedding)
    
    # Different embedding
    different_embedding = np.random.randn(512)
    different_embedding = different_embedding / np.linalg.norm(different_embedding)
    
    print("Testing verifier...")
    
    # Test similar
    result = verifier.verify(similar_embedding, [base_embedding])
    print(f"\nSimilar embedding test:")
    print(f"  Distance: {result['distance']:.4f}")
    print(f"  Confidence: {result['confidence']:.1f}%")
    print(f"  Verified: {result['verified']}")
    
    # Test different
    result = verifier.verify(different_embedding, [base_embedding])
    print(f"\nDifferent embedding test:")
    print(f"  Distance: {result['distance']:.4f}")
    print(f"  Confidence: {result['confidence']:.1f}%")
    print(f"  Verified: {result['verified']}")
    
    print("\nVerifier test complete!")


if __name__ == "__main__":
    test_verifier()
