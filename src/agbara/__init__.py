"""
Agbara - The Self-Evolving Omni-Modal Intelligence System
Core initialization and main entry point.
"""

__version__ = "1.0.0"
__author__ = "Agbara-Okenze + Agbara AI"
__license__ = "Apache 2.0"

from .expert_router import ExpertRouter
from .expert_manager import ExpertManager
from .memory_system import MemorySystem
from .cache_manager import CacheManager
from .response_engine import ResponseEngine
from .streaming_engine import StreamingEngine

class Agbara:
    """
    Main Agbara class - The Self-Evolving Omni-Modal Intelligence System.
    
    Combines 20+ world-class open-source models into a unified,
    hyper-optimized intelligence platform with Igbo language support.
    """
    
    def __init__(
        self,
        config_path: str = None,
        gpu_memory: int = 80 * 1024,  # 80GB default
        quantization: str = "4bit",
        cache_dir: str = "/tmp/agbara_cache",
        igbo_enabled: bool = True
    ):
        """
        Initialize Agbara.
        
        Args:
            config_path: Path to configuration file
            gpu_memory: Available GPU memory in MB
            quantization: Quantization level ("4bit", "8bit", "fp16")
            cache_dir: Directory for caching
            igbo_enabled: Enable Igbo language expert
        """
        # Initialize core components
        self.memory_system = MemorySystem(cache_dir=cache_dir)
        self.cache_manager = CacheManager(
            cache_dir=cache_dir,
            semantic_cache_size=10000
        )
        self.expert_manager = ExpertManager(
            gpu_memory=gpu_memory,
            quantization=quantization,
            cache_dir=cache_dir
        )
        self.router = ExpertRouter(
            expert_manager=self.expert_manager,
            cache_manager=self.cache_manager
        )
        self.response_engine = ResponseEngine(
            expert_manager=self.expert_manager,
            memory_system=self.memory_system
        )
        self.streaming_engine = StreamingEngine(
            response_engine=self.response_engine
        )
        
        # Load Igbo expert if enabled
        self.igbo_enabled = igbo_enabled
        if igbo_enabled:
            from ..culture.igbo_language_expert import IgboLanguageExpert
            self.igbo_expert = IgboLanguageExpert()
        
    def process(
        self,
        query: str,
        modality: str = "text",
        stream: bool = False,
        context: list = None,
        igbo_mode: bool = False
    ):
        """
        Process a query through the Agbara system.
        
        Args:
            query: Input query
            modality: Input modality (text, image, audio, video)
            stream: Enable streaming output
            context: Previous context
            igbo_mode: Enable Igbo language mode
            
        Returns:
            Response from the appropriate expert(s)
        """
        # Check cache first
        cached = self.cache_manager.get(query)
        if cached:
            return cached
            
        # Route to appropriate expert(s)
        expert_assignments = self.router.route(
            query=query,
            modality=modality,
            igbo_mode=igbo_mode
        )
        
        # Execute through response engine
        if stream:
            return self.streaming_engine.stream(
                query=query,
                experts=expert_assignments,
                context=context
            )
        else:
            response = self.response_engine.generate(
                query=query,
                experts=expert_assignments,
                context=context
            )
            
            # Cache the response
            self.cache_manager.set(query, response)
            
            return response
    
    async def process_async(
        self,
        query: str,
        modality: str = "text",
        stream: bool = False,
        context: list = None,
        igbo_mode: bool = False
    ):
        """Async version of process."""
        # Check cache first
        cached = await self.cache_manager.get_async(query)
        if cached:
            return cached
            
        # Route to appropriate expert(s)
        expert_assignments = await self.router.route_async(
            query=query,
            modality=modality,
            igbo_mode=igbo_mode
        )
        
        # Execute through response engine
        if stream:
            async for chunk in self.streaming_engine.stream_async(
                query=query,
                experts=expert_assignments,
                context=context
            ):
                yield chunk
        else:
            response = await self.response_engine.generate_async(
                query=query,
                experts=expert_assignments,
                context=context
            )
            
            # Cache the response
            await self.cache_manager.set_async(query, response)
            
            return response
    
    def load_expert(self, expert_name: str):
        """Load a specific expert into memory."""
        return self.expert_manager.load_expert(expert_name)
    
    def unload_expert(self, expert_name: str):
        """Unload a specific expert from memory."""
        return self.expert_manager.unload_expert(expert_name)
    
    def list_experts(self) -> list:
        """List all available experts."""
        return self.expert_manager.list_experts()
    
    def get_status(self) -> dict:
        """Get system status."""
        return {
            "version": __version__,
            "gpu_memory_used": self.expert_manager.get_memory_usage(),
            "gpu_memory_total": self.expert_manager.gpu_memory,
            "cache_size": self.cache_manager.size(),
            "experts_loaded": self.expert_manager.get_loaded_experts(),
            "igbo_enabled": self.igbo_enabled
        }


# Convenience function
def create_agbara(**kwargs):
    """Create and return an Agbara instance."""
    return Agbara(**kwargs)
