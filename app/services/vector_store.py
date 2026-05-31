"""Vector store service using ChromaDB for exercise embeddings."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from functools import lru_cache
import logging
import os
import hashlib
import threading

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing exercise embeddings in ChromaDB."""
    
    # Class-level lock for thread-safe initialization
    _init_lock = threading.Lock()
    _initialized_collections = set()
    
    def __init__(self, db_path: str, embedding_model_name: str):
        """Initialize the vector store service.
        
        Args:
            db_path: Path to ChromaDB persistent storage
            embedding_model_name: Name of the sentence-transformers model
        """
        self.db_path = db_path
        self.embedding_model_name = embedding_model_name
        
        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        logger.info("Embedding model loaded successfully")
        
        self.collection = None
        self._embedding_cache = {}  # Simple cache for query embeddings
        self._cache_max_size = 100
    
    def initialize_collection(self):
        """Create or load the exercise embeddings collection."""
        try:
            self.collection = self.client.get_or_create_collection(
                name="exercise_embeddings",
                metadata={"description": "Exercise database embeddings for RAG"}
            )
            logger.info(f"Collection initialized with {self.collection.count()} exercises")
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def create_exercise_document(self, exercise: Dict) -> str:
        """Create rich text document for embedding.
        
        Args:
            exercise: Exercise dictionary from ExerciseDB
            
        Returns:
            Formatted text document for embedding
        """
        # Extract fields with defaults
        name = exercise.get('name', '')
        target_muscles = ', '.join(exercise.get('targetMuscles', []))
        body_parts = ', '.join(exercise.get('bodyParts', []))
        equipment = ', '.join(exercise.get('equipments', []))
        secondary_muscles = ', '.join(exercise.get('secondaryMuscles', []))
        
        # Get first 3 instruction steps
        instructions = exercise.get('instructions', [])
        instruction_summary = ' '.join(instructions[:3]) if instructions else ''
        
        # Create rich document
        doc = f"""Exercise: {name}
Target Muscles: {target_muscles}
Body Parts: {body_parts}
Equipment: {equipment}
Secondary Muscles: {secondary_muscles}
Instructions: {instruction_summary}"""
        
        return doc
    
    async def add_exercises(self, exercises: List[Dict]):
        """Add exercises to the vector store with thread-safe initialization.
        
        Args:
            exercises: List of exercise dictionaries from ExerciseDB
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized. Call initialize_collection() first.")
        
        # Thread-safe check and initialization
        collection_key = f"{self.db_path}:exercise_embeddings"
        
        with self._init_lock:
            # Double-check if already populated
            if self.collection.count() > 0:
                logger.info(f"Vector store already contains {self.collection.count()} exercises, skipping...")
                return
            
            # Mark as being initialized
            if collection_key in self._initialized_collections:
                logger.info("Another thread is initializing the collection, skipping...")
                return
            
            self._initialized_collections.add(collection_key)
        
        logger.info(f"Adding {len(exercises)} exercises to vector store...")
        
        # Deduplicate exercises by ID (keep first occurrence)
        seen_ids = set()
        unique_exercises = []
        duplicates_count = 0
        
        for exercise in exercises:
            exercise_id = exercise.get("exerciseId", exercise.get("id", ""))
            if exercise_id not in seen_ids:
                seen_ids.add(exercise_id)
                unique_exercises.append(exercise)
            else:
                duplicates_count += 1
        
        if duplicates_count > 0:
            logger.warning(f"Found {duplicates_count} duplicate exercise IDs, keeping only unique exercises")
            logger.info(f"Processing {len(unique_exercises)} unique exercises (removed {duplicates_count} duplicates)")
        
        documents = []
        metadatas = []
        ids = []
        
        for exercise in unique_exercises:
            # Create document for embedding
            doc = self.create_exercise_document(exercise)
            documents.append(doc)
            
            # Store metadata
            exercise_id = exercise.get("exerciseId", exercise.get("id", ""))
            metadatas.append({
                "exercise_id": exercise_id,
                "name": exercise.get("name", ""),
                "target_muscles": ",".join(exercise.get("targetMuscles", [])),
                "body_parts": ",".join(exercise.get("bodyParts", [])),
                "equipment": ",".join(exercise.get("equipments", [])),
                "gif_url": exercise.get("gifUrl", "")
            })
            
            ids.append(exercise_id)
        
        # Generate embeddings in batches
        batch_size = 32
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(
                batch_docs,
                show_progress_bar=True,
                convert_to_numpy=True
            ).tolist()
            
            # Add to collection
            self.collection.add(
                documents=batch_docs,
                embeddings=embeddings,
                metadatas=batch_metas,
                ids=batch_ids
            )
        
        logger.info(f"Successfully added {len(exercises)} exercises to vector store")
    
    def search_exercises(
        self,
        query: str,
        filters: Optional[Dict] = None,
        n_results: int = 50
    ) -> List[Dict]:
        """Search for exercises using semantic search.
        
        Args:
            query: Search query text
            filters: Optional metadata filters
            n_results: Number of results to return
            
        Returns:
            List of exercise dictionaries with metadata
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized. Call initialize_collection() first.")
        
        try:
            # Check cache first for performance
            cache_key = hashlib.md5(query.encode()).hexdigest()
            
            if cache_key in self._embedding_cache:
                logger.debug(f"Using cached embedding for query: {query[:50]}...")
                query_embedding = self._embedding_cache[cache_key]
            else:
                # Generate query embedding
                query_embedding = self.embedding_model.encode([query]).tolist()
                
                # Add to cache (with size limit)
                if len(self._embedding_cache) >= self._cache_max_size:
                    # Remove oldest entry (simple FIFO)
                    self._embedding_cache.pop(next(iter(self._embedding_cache)))
                self._embedding_cache[cache_key] = query_embedding
            
            # Search with optional filters
            search_kwargs = {
                "query_embeddings": query_embedding,
                "n_results": n_results
            }
            
            if filters:
                search_kwargs["where"] = filters
            
            results = self.collection.query(**search_kwargs)
            
            # Format results
            exercises = []
            for i in range(len(results["ids"][0])):
                exercises.append({
                    "id": results["ids"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None,
                    "document": results["documents"][0][i] if "documents" in results else None
                })
            
            logger.info(f"Found {len(exercises)} exercises for query: '{query[:50]}...'")
            return exercises
            
        except Exception as e:
            logger.error(f"Error searching exercises: {e}")
            raise
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        if self.collection is None:
            return {"status": "not_initialized", "count": 0}
        
        return {
            "status": "ready",
            "count": self.collection.count(),
            "name": self.collection.name
        }

# Made with Bob
