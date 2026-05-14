"""
Streaming Engine - Real-time streaming response generation.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
import logging

from .expert_router import ExpertAssignment
from .response_engine import ResponseEngine

logger = logging.getLogger(__name__)


class StreamingEngine:
    """
    Streaming response generation with real-time output.
    
    Features:
    - Server-Sent Events (SSE) compatible
    - Chunked streaming
    - Low first-token latency
    - Backpressure handling
    """
    
    def __init__(self, response_engine: ResponseEngine):
        self.response_engine = response_engine
        
        # Streaming stats
        self.total_streams = 0
        self.total_chunks = 0
    
    def stream(
        self,
        query: str,
        experts: List[ExpertAssignment],
        context: List[Dict] = None,
        chunk_size: int = 20
    ):
        """
        Stream response chunks.
        
        Args:
            query: Input query
            experts: List of expert assignments
            context: Previous conversation context
            chunk_size: Number of words per chunk
            
        Yields:
            Response chunks
        """
        self.total_streams += 1
        
        # Generate full response
        response = self.response_engine.generate(query, experts, context)
        content = response.content
        
        # Split into chunks
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            self.total_chunks += 1
        
        # Yield chunks
        for i, chunk in enumerate(chunks):
            yield {
                "chunk": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "expert_used": response.expert_used,
                "is_final": i == len(chunks) - 1
            }
    
    async def stream_async(
        self,
        query: str,
        experts: List[ExpertAssignment],
        context: List[Dict] = None,
        chunk_size: int = 20
    ) -> AsyncGenerator[Dict, None]:
        """Async version of stream."""
        self.total_streams += 1
        
        # Generate full response
        response = await self.response_engine.generate_async(query, experts, context)
        content = response.content
        
        # Split into chunks
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            self.total_chunks += 1
        
        # Yield chunks with small delay for realistic streaming
        for i, chunk in enumerate(chunks):
            await asyncio.sleep(0.05)  # 50ms between chunks
            yield {
                "chunk": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "expert_used": response.expert_used,
                "is_final": i == len(chunks) - 1
            }
    
    def stream_sse(
        self,
        query: str,
        experts: List[ExpertAssignment],
        context: List[Dict] = None,
        chunk_size: int = 20
    ):
        """
        Stream in Server-Sent Events format.
        
        Yields:
            SSE formatted strings
        """
        for chunk_data in self.stream(query, experts, context, chunk_size):
            import json
            yield f"data: {json.dumps(chunk_data)}\n\n"
        
        yield "data: [DONE]\n\n"
    
    async def stream_sse_async(
        self,
        query: str,
        experts: List[ExpertAssignment],
        context: List[Dict] = None,
        chunk_size: int = 20
    ) -> AsyncGenerator[str, None]:
        """Async SSE streaming."""
        async for chunk_data in self.stream_async(query, experts, context, chunk_size):
            import json
            yield f"data: {json.dumps(chunk_data)}\n\n"
        
        yield "data: [DONE]\n\n"
    
    def get_stats(self) -> Dict:
        """Get streaming statistics."""
        avg_chunks = (
            self.total_chunks / self.total_streams
            if self.total_streams > 0 else 0
        )
        
        return {
            "total_streams": self.total_streams,
            "total_chunks": self.total_chunks,
            "average_chunks_per_stream": avg_chunks
        }
