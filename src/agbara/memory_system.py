"""
Memory System - Vector database and knowledge graph for persistent memory.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A memory entry in the system."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    importance: float = 0.5


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph."""
    id: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: List[Tuple[str, str]] = field(default_factory=list)  # (relation, target_id)


class VectorStore:
    """
    Simple vector store for semantic search.
    
    In production, this would be replaced with:
    - FAISS for efficient similarity search
    - Chroma for persistent vector storage
    - Pinecone for cloud vector database
    """
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.vectors: Dict[str, List[float]] = {}
        self.metadata: Dict[str, Dict] = {}
    
    def add(self, id: str, vector: List[float], metadata: Dict = None):
        """Add a vector to the store."""
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: {len(vector)} != {self.dimension}")
        self.vectors[id] = vector
        self.metadata[id] = metadata or {}
    
    def get(self, id: str) -> Optional[Tuple[List[float], Dict]]:
        """Get a vector by ID."""
        if id in self.vectors:
            return (self.vectors[id], self.metadata[id])
        return None
    
    def delete(self, id: str):
        """Delete a vector."""
        self.vectors.pop(id, None)
        self.metadata.pop(id, None)
    
    def search(self, query_vector: List[float], k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Search for similar vectors using cosine similarity."""
        if not self.vectors:
            return []
        
        # Simple cosine similarity (in production, use FAISS)
        results = []
        query_norm = sum(v * v for v in query_vector) ** 0.5
        
        for id, vector in self.vectors.items():
            dot_product = sum(a * b for a, b in zip(query_vector, vector))
            vec_norm = sum(v * v for v in vector) ** 0.5
            
            if query_norm > 0 and vec_norm > 0:
                similarity = dot_product / (query_norm * vec_norm)
            else:
                similarity = 0
            
            results.append((id, similarity, self.metadata[id]))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def clear(self):
        """Clear all vectors."""
        self.vectors.clear()
        self.metadata.clear()
    
    def size(self) -> int:
        """Get number of vectors."""
        return len(self.vectors)


class KnowledgeGraph:
    """
    Simple knowledge graph for entity relationships.
    
    In production, this would be replaced with:
    - Neo4j for graph database
    - NetworkX for in-memory graph
    """
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.index_by_label: Dict[str, List[str]] = {}
    
    def add_node(self, id: str, label: str, properties: Dict = None):
        """Add a node to the graph."""
        node = KnowledgeNode(
            id=id,
            label=label,
            properties=properties or {}
        )
        self.nodes[id] = node
        
        # Update label index
        if label not in self.index_by_label:
            self.index_by_label[label] = []
        self.index_by_label[label].append(id)
    
    def add_relationship(self, source_id: str, relation: str, target_id: str):
        """Add a relationship between nodes."""
        if source_id in self.nodes:
            self.nodes[source_id].relationships.append((relation, target_id))
    
    def get_node(self, id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        return self.nodes.get(id)
    
    def get_nodes_by_label(self, label: str) -> List[KnowledgeNode]:
        """Get all nodes with a given label."""
        node_ids = self.index_by_label.get(label, [])
        return [self.nodes[id] for id in node_ids if id in self.nodes]
    
    def get_neighbors(self, node_id: str, relation: str = None) -> List[KnowledgeNode]:
        """Get neighboring nodes."""
        if node_id not in self.nodes:
            return []
        
        neighbors = []
        for rel, target_id in self.nodes[node_id].relationships:
            if relation is None or rel == relation:
                if target_id in self.nodes:
                    neighbors.append(self.nodes[target_id])
        
        return neighbors
    
    def search(self, query: str) -> List[KnowledgeNode]:
        """Search nodes by property values."""
        results = []
        query_lower = query.lower()
        
        for node in self.nodes.values():
            # Search in properties
            for value in node.properties.values():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(node)
                    break
        
        return results


class MemorySystem:
    """
    Unified memory system combining vector store and knowledge graph.
    
    Features:
    - Semantic memory (facts, concepts)
    - Episodic memory (conversations, events)
    - Working memory (current context)
    - Knowledge graph (entity relationships)
    """
    
    def __init__(
        self,
        cache_dir: str = "/tmp/agbara_memory",
        embedding_dimension: int = 768
    ):
        """
        Initialize the memory system.
        
        Args:
            cache_dir: Directory for persistent storage
            embedding_dimension: Dimension of embedding vectors
        """
        self.cache_dir = cache_dir
        self.embedding_dimension = embedding_dimension
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize components
        self.semantic_memory = VectorStore(dimension=embedding_dimension)
        self.knowledge_graph = KnowledgeGraph()
        
        # Working memory (current session)
        self.working_memory: List[MemoryEntry] = []
        self.max_working_memory = 10
        
        # Episodic memory (conversation history)
        self.episodic_memory: List[MemoryEntry] = []
        self.max_episodic_memory = 100
        
        # Load persisted memory
        self._load_memory()
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for content."""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text.
        
        In production, this would use:
        - sentence-transformers
        - OpenAI embeddings
        - Local embedding model
        """
        # Placeholder: return random embedding for now
        # In production, use actual embedding model
        import random
        random.seed(hash(text) % (2**32))
        return [random.gauss(0, 1) for _ in range(self.embedding_dimension)]
    
    def remember(
        self,
        content: str,
        memory_type: str = "semantic",
        metadata: Dict = None,
        importance: float = 0.5
    ) -> str:
        """
        Store something in memory.
        
        Args:
            content: Content to remember
            memory_type: Type of memory (semantic, episodic, working)
            metadata: Additional metadata
            importance: Importance score (0.0-1.0)
            
        Returns:
            Memory entry ID
        """
        entry_id = self._generate_id(content)
        embedding = self._get_embedding(content)
        
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            importance=importance
        )
        
        if memory_type == "semantic":
            self.semantic_memory.add(entry_id, embedding, {
                "content": content,
                "importance": importance,
                **(metadata or {})
            })
        elif memory_type == "episodic":
            self.episodic_memory.append(entry)
            if len(self.episodic_memory) > self.max_episodic_memory:
                # Remove least important
                self.episodic_memory.sort(key=lambda x: x.importance)
                self.episodic_memory = self.episodic_memory[-self.max_episodic_memory:]
        elif memory_type == "working":
            self.working_memory.append(entry)
            if len(self.working_memory) > self.max_working_memory:
                self.working_memory.pop(0)
        
        # Persist
        self._save_memory()
        
        return entry_id
    
    def recall(
        self,
        query: str,
        memory_types: List[str] = None,
        k: int = 5
    ) -> List[MemoryEntry]:
        """
        Recall relevant memories.
        
        Args:
            query: Search query
            memory_types: Types of memory to search
            k: Number of results
            
        Returns:
            List of relevant memory entries
        """
        if memory_types is None:
            memory_types = ["semantic", "episodic", "working"]
        
        results = []
        query_embedding = self._get_embedding(query)
        
        # Search semantic memory
        if "semantic" in memory_types:
            semantic_results = self.semantic_memory.search(query_embedding, k=k)
            for id, similarity, metadata in semantic_results:
                entry = MemoryEntry(
                    id=id,
                    content=metadata.get("content", ""),
                    embedding=self.semantic_memory.vectors.get(id),
                    metadata=metadata,
                    importance=metadata.get("importance", 0.5)
                )
                results.append(entry)
        
        # Search episodic memory
        if "episodic" in memory_types:
            for entry in self.episodic_memory:
                if query.lower() in entry.content.lower():
                    results.append(entry)
        
        # Search working memory
        if "working" in memory_types:
            for entry in self.working_memory:
                if query.lower() in entry.content.lower():
                    results.append(entry)
        
        # Sort by importance and recency
        results.sort(key=lambda x: x.importance, reverse=True)
        
        return results[:k]
    
    def forget(self, entry_id: str):
        """Remove a memory entry."""
        self.semantic_memory.delete(entry_id)
        self.episodic_memory = [e for e in self.episodic_memory if e.id != entry_id]
        self.working_memory = [e for e in self.working_memory if e.id != entry_id]
        self._save_memory()
    
    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        properties: Dict = None
    ):
        """Add an entity to the knowledge graph."""
        self.knowledge_graph.add_node(entity_id, entity_type, properties)
        self._save_memory()
    
    def add_relation(
        self,
        source_id: str,
        relation: str,
        target_id: str
    ):
        """Add a relationship between entities."""
        self.knowledge_graph.add_relationship(source_id, relation, target_id)
        self._save_memory()
    
    def query_entities(self, entity_type: str = None, query: str = None) -> List[KnowledgeNode]:
        """Query entities from the knowledge graph."""
        if entity_type:
            return self.knowledge_graph.get_nodes_by_label(entity_type)
        elif query:
            return self.knowledge_graph.search(query)
        return []
    
    def clear_working_memory(self):
        """Clear working memory."""
        self.working_memory.clear()
    
    def _save_memory(self):
        """Save memory to disk."""
        memory_file = os.path.join(self.cache_dir, "memory.json")
        
        data = {
            "episodic": [
                {
                    "id": e.id,
                    "content": e.content,
                    "metadata": e.metadata,
                    "importance": e.importance
                }
                for e in self.episodic_memory
            ],
            "knowledge_graph": {
                "nodes": {
                    id: {
                        "label": n.label,
                        "properties": n.properties,
                        "relationships": n.relationships
                    }
                    for id, n in self.knowledge_graph.nodes.items()
                }
            }
        }
        
        with open(memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_memory(self):
        """Load memory from disk."""
        memory_file = os.path.join(self.cache_dir, "memory.json")
        
        if not os.path.exists(memory_file):
            return
        
        try:
            with open(memory_file, 'r') as f:
                data = json.load(f)
            
            # Load episodic memory
            for e in data.get("episodic", []):
                entry = MemoryEntry(
                    id=e["id"],
                    content=e["content"],
                    metadata=e.get("metadata", {}),
                    importance=e.get("importance", 0.5)
                )
                self.episodic_memory.append(entry)
            
            # Load knowledge graph
            for id, node_data in data.get("knowledge_graph", {}).get("nodes", {}).items():
                self.knowledge_graph.add_node(
                    id=id,
                    label=node_data["label"],
                    properties=node_data.get("properties", {})
                )
                for rel, target in node_data.get("relationships", []):
                    self.knowledge_graph.add_relationship(id, rel, target)
            
            logger.info(f"Loaded memory from {memory_file}")
            
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        return {
            "semantic_memory_size": self.semantic_memory.size(),
            "episodic_memory_size": len(self.episodic_memory),
            "working_memory_size": len(self.working_memory),
            "knowledge_graph_nodes": len(self.knowledge_graph.nodes),
            "knowledge_graph_labels": list(self.knowledge_graph.index_by_label.keys())
        }
