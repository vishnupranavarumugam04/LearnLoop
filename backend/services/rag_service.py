"""
RAG Service - Retrieval-Augmented Generation
Provides context-aware AI responses using document embeddings
Optimized for FREE TIER usage
"""
import json
from typing import List, Dict, Optional, Tuple
import numpy as np

class RAGService:
    """RAG service for context-aware learning"""
    
    def __init__(self):
        """Initialize RAG service"""
        self.embeddings_cache = {}  # In-memory cache to reduce API calls
        self.use_rag = False  # Will be enabled when Bedrock is available
        
        # Try to initialize Bedrock
        try:
            from services.bedrock_service import bedrock_service
            self.bedrock_service = bedrock_service
            self.use_rag = bedrock_service.use_bedrock
        except Exception as e:
            print(f"ℹ️  RAG service in fallback mode: {e}")
            self.bedrock_service = None
    
    def generate_material_embedding(self, material_id: int, text: str) -> Optional[List[float]]:
        """
        Generate and cache embedding for study material
        Args:
            material_id: ID of the material
            text: Material text content
        Returns:
            Embedding vector or None
        """
        if not self.use_rag or not self.bedrock_service:
            return None
        
        # Check cache first
        cache_key = f"material_{material_id}"
        if cache_key in self.embeddings_cache:
            print(f"✅ Using cached embedding for material {material_id}")
            return self.embeddings_cache[cache_key]
        
        # Generate new embedding
        # Truncate text to reduce cost (first 2000 chars usually sufficient)
        truncated_text = text[:2000]
        embedding = self.bedrock_service.get_embedding(truncated_text)
        
        if embedding:
            self.embeddings_cache[cache_key] = embedding
            print(f"✅ Generated and cached embedding for material {material_id}")
        
        return embedding
    
    def find_relevant_content(self, 
                             query: str, 
                             material_texts: List[Tuple[int, str]], 
                             top_k: int = 3) -> List[Tuple[int, str, float]]:
        """
        Find most relevant material content for a query
        Args:
            query: User query
            material_texts: List of (material_id, text) tuples
            top_k: Number of top results to return
        Returns:
            List of (material_id, text, similarity_score) tuples
        """
        if not self.use_rag or not self.bedrock_service:
            # Fallback: return first material
            if material_texts:
                return [(material_texts[0][0], material_texts[0][1], 1.0)]
            return []
        
        # Generate query embedding
        query_embedding = self.bedrock_service.get_embedding(query)
        if not query_embedding:
            # Fallback
            if material_texts:
                return [(material_texts[0][0], material_texts[0][1], 1.0)]
            return []
        
        # Calculate similarities
        similarities = []
        for material_id, text in material_texts:
            # Generate or retrieve material embedding
            material_embedding = self.generate_material_embedding(material_id, text)
            if not material_embedding:
                continue
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, material_embedding)
            similarities.append((material_id, text, similarity))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[2], reverse=True)
        return similarities[:top_k]
    
    def build_context_for_conversation(self, 
                                      query: str, 
                                      user_id: int,
                                      material_id: Optional[int] = None) -> str:
        """
        Build context for AI conversation using RAG
        Args:
            query: User query
            user_id: User ID
            material_id: Optional specific material to focus on
        Returns:
            Context string for AI prompt
        """
        try:
            from database import get_db
            
            conn = get_db()
            cursor = conn.cursor()
            
            # Get relevant materials
            if material_id:
                cursor.execute(
                    "SELECT id, full_text FROM study_materials WHERE id = ? AND user_id = ?",
                    (material_id, user_id)
                )
            else:
                cursor.execute(
                    "SELECT id, full_text FROM study_materials WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 5",
                    (user_id,)
                )
            
            materials = cursor.fetchall()
            conn.close()
            
            if not materials:
                return ""
            
            # Convert to list of tuples
            material_texts = [(row['id'], row['full_text'] or "") for row in materials if row['full_text']]
            
            # Find relevant content
            relevant = self.find_relevant_content(query, material_texts, top_k=2)
            
            # Build context
            if relevant:
                context_parts = []
                for material_id, text, score in relevant:
                    # Extract most relevant excerpt (first 500 chars)
                    excerpt = text[:500]
                    context_parts.append(f"[Relevance: {score:.2f}]\n{excerpt}")
                
                context = "\n\n---\n\n".join(context_parts)
                return f"\nRELEVANT CONTEXT:\n{context}\n"
            
            return ""
            
        except Exception as e:
            print(f"⚠️  Context building failed: {e}")
            return ""
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            print(f"⚠️  Similarity calculation failed: {e}")
            return 0.0
    
    def enhance_knowledge_graph(self, user_id: int, material_id: int, concepts: List[str]):
        """
        Use RAG to enhance knowledge graph with related concepts
        Args:
            user_id: User ID
            material_id: Material ID
            concepts: List of concepts to expand
        """
        if not self.use_rag:
            return
        
        try:
            from database import add_knowledge_node, add_knowledge_edge, get_material_by_id
            
            # Get material content
            material = get_material_by_id(material_id)
            if not material:
                return
            
            material_name = material.get('filename', 'Unknown')
            
            # For each concept, find related concepts in the material
            for concept in concepts:
                query = f"What are the key topics related to {concept}?"
                relevant_content = self.build_context_for_conversation(query, user_id, material_id)
                
                # Add concept to knowledge graph
                add_knowledge_node(
                    user_id, 
                    concept, 
                    subject=material_name,
                    mastery_level=50,
                    description=f"Learning from {material_name}"
                )
                
                # Link to material
                add_knowledge_edge(
                    user_id,
                    material_name,
                    concept,
                    relationship_type="contains",
                    strength=0.7
                )
        except Exception as e:
            print(f"⚠️  Knowledge graph enhancement failed: {e}")

# Global RAG service instance
rag_service = RAGService()

# Convenience functions
def generate_material_embedding(material_id: int, text: str) -> Optional[List[float]]:
    """Generate embedding for material"""
    return rag_service.generate_material_embedding(material_id, text)

def build_context_for_conversation(query: str, user_id: int, material_id: Optional[int] = None) -> str:
    """Build RAG context for conversation"""
    return rag_service.build_context_for_conversation(query, user_id, material_id)

def enhance_knowledge_graph(user_id: int, material_id: int, concepts: List[str]):
    """Enhance knowledge graph with RAG"""
    return rag_service.enhance_knowledge_graph(user_id, material_id, concepts)
