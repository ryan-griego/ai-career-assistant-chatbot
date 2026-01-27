"""Semantic cache system for reducing OpenAI API calls"""

import sqlite3
import json
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import numpy as np
from openai import OpenAI
from pathlib import Path


class SemanticCache:
    """
    Semantic cache that uses embeddings to find similar queries.

    When a user asks a question, we:
    1. Generate embedding for the query
    2. Search cache for similar queries (cosine similarity)
    3. If similarity > threshold, return cached response
    4. Otherwise, generate new response and cache it
    """

    def __init__(self,
                 db_path: str = "cache.db",
                 similarity_threshold: float = 0.92,
                 cache_ttl_days: int = 30,
                 openai_client: Optional[OpenAI] = None):
        """
        Initialize semantic cache

        Args:
            db_path: Path to SQLite database
            similarity_threshold: Cosine similarity threshold (0.92 = very similar)
            cache_ttl_days: Number of days to keep cache entries
            openai_client: OpenAI client for generating embeddings
        """
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self.cache_ttl_days = cache_ttl_days
        self.openai_client = openai_client or OpenAI()
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Cache table for storing query-response pairs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS response_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    query_embedding BLOB NOT NULL,
                    response TEXT NOT NULL,
                    context_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            ''')

            # Index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_context_hash
                ON response_cache(context_hash)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON response_cache(created_at)
            ''')

            conn.commit()

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI's embedding model"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",  # Cheaper and faster than ada-002
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0

        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _embedding_to_blob(self, embedding: List[float]) -> bytes:
        """Convert embedding list to binary blob for storage"""
        return json.dumps(embedding).encode('utf-8')

    def _blob_to_embedding(self, blob: bytes) -> List[float]:
        """Convert binary blob back to embedding list"""
        return json.loads(blob.decode('utf-8'))

    def get_cached_response(self,
                           query: str,
                           context_hash: str) -> Optional[Tuple[str, float]]:
        """
        Search cache for similar query and return cached response if found

        Args:
            query: User's query
            context_hash: Hash of current context (to ensure cache is valid)

        Returns:
            Tuple of (cached_response, similarity_score) or None if no match
        """
        # Generate embedding for query
        query_embedding = self._generate_embedding(query)
        if not query_embedding:
            return None

        # Search cache for similar queries with matching context
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all cached queries with same context hash
            cursor.execute('''
                SELECT id, query, query_embedding, response, created_at
                FROM response_cache
                WHERE context_hash = ?
                AND created_at > ?
                ORDER BY created_at DESC
            ''', (
                context_hash,
                datetime.now() - timedelta(days=self.cache_ttl_days)
            ))

            best_match = None
            best_similarity = 0.0

            for row in cursor.fetchall():
                cache_id, cached_query, cached_embedding_blob, cached_response, created_at = row
                cached_embedding = self._blob_to_embedding(cached_embedding_blob)

                # Calculate similarity
                similarity = self._cosine_similarity(query_embedding, cached_embedding)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (cache_id, cached_response)

            # If best match exceeds threshold, return it
            if best_match and best_similarity >= self.similarity_threshold:
                cache_id, response = best_match

                # Update access statistics
                cursor.execute('''
                    UPDATE response_cache
                    SET last_accessed = CURRENT_TIMESTAMP,
                        access_count = access_count + 1
                    WHERE id = ?
                ''', (cache_id,))
                conn.commit()

                print(f"✅ Cache hit! Similarity: {best_similarity:.4f} (saved OpenAI call)")
                return (response, best_similarity)

        return None

    def cache_response(self,
                      query: str,
                      response: str,
                      context_hash: str):
        """
        Cache a query-response pair

        Args:
            query: User's query
            response: AI's response
            context_hash: Hash of current context
        """
        # Generate embedding for query
        query_embedding = self._generate_embedding(query)
        if not query_embedding:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO response_cache
                (query, query_embedding, response, context_hash)
                VALUES (?, ?, ?, ?)
            ''', (
                query,
                self._embedding_to_blob(query_embedding),
                response,
                context_hash
            ))

            conn.commit()
            print("💾 Response cached for future queries")

    def clean_old_entries(self):
        """Remove cache entries older than TTL"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=self.cache_ttl_days)
            cursor.execute('''
                DELETE FROM response_cache
                WHERE created_at < ?
            ''', (cutoff_date,))

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                print(f"🧹 Cleaned {deleted_count} old cache entries")

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM response_cache')
            total_entries = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(access_count) FROM response_cache')
            total_accesses = cursor.fetchone()[0] or 0

            cursor.execute('''
                SELECT COUNT(*) FROM response_cache
                WHERE access_count > 1
            ''')
            reused_entries = cursor.fetchone()[0]

            cursor.execute('''
                SELECT AVG(access_count) FROM response_cache
                WHERE access_count > 1
            ''')
            avg_reuse = cursor.fetchone()[0] or 0

            return {
                'total_entries': total_entries,
                'total_accesses': total_accesses,
                'reused_entries': reused_entries,
                'avg_reuse': round(avg_reuse, 2),
                'cache_hit_rate': f"{(reused_entries / total_entries * 100) if total_entries > 0 else 0:.1f}%"
            }

    def clear_cache(self):
        """Clear entire cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM response_cache')
            conn.commit()
            print("🗑️ Cache cleared")


def test_semantic_cache():
    """Test semantic cache functionality"""
    from openai import OpenAI
    import os
    from dotenv import load_dotenv

    load_dotenv()
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    cache = SemanticCache(
        db_path="test_cache.db",
        similarity_threshold=0.90,
        openai_client=client
    )

    # Test caching
    context_hash = "test_context_v1"

    # Cache a response
    cache.cache_response(
        query="What companies has Ryan worked for?",
        response="Ryan has worked for Company A, Company B, and Company C.",
        context_hash=context_hash
    )

    # Try to retrieve with similar query
    similar_queries = [
        "What companies has Ryan worked for?",  # Exact match
        "Which companies did Ryan work at?",    # Similar
        "Where has Ryan been employed?",        # Similar meaning
        "What is Ryan's favorite color?",       # Different topic
    ]

    for query in similar_queries:
        print(f"\n🔍 Query: {query}")
        result = cache.get_cached_response(query, context_hash)
        if result:
            response, similarity = result
            print(f"✅ Found cached response (similarity: {similarity:.4f})")
            print(f"📝 Response: {response}")
        else:
            print("❌ No cache hit")

    # Show stats
    print("\n📊 Cache Stats:")
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_semantic_cache()
