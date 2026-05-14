"""
Expert Manager - GPU memory and model management for all experts.
"""

import asyncio
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import logging

logger = logging.getLogger(__name__)


class ExpertState(Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


@dataclass
class ExpertConfig:
    """Configuration for an expert."""
    name: str
    model_id: str
    memory_mb: int
    modality: str
    specialties: List[str]
    quantization: str = "4bit"
    flash_attention: bool = True
    vllm_enabled: bool = True
    state: ExpertState = ExpertState.UNLOADED
    loaded_at: Optional[float] = None
    error_message: Optional[str] = None


class ExpertManager:
    """
    Manages GPU memory and model loading/unloading for all experts.
    
    Features:
    - Memory-aware expert loading
    - LRU eviction policy
    - Quantization support (4bit, 8bit, fp16)
    - Flash Attention 2 optimization
    - vLLM integration for fast inference
    - Parallel expert loading
    """
    
    # All available experts
    EXPERT_REGISTRY = {
        # Text Experts
        "llama4-70b": ExpertConfig(
            name="llama4-70b",
            model_id="meta-llama/Llama-4-70B",
            memory_mb=35000,
            modality="text",
            specialties=["reasoning", "general", "long-context"]
        ),
        "qwen3-72b": ExpertConfig(
            name="qwen3-72b",
            model_id="Qwen/Qwen3-72B",
            memory_mb=36000,
            modality="text",
            specialties=["multilingual", "scientific", "math"]
        ),
        "deepseek-coder": ExpertConfig(
            name="deepseek-coder",
            model_id="deepseek-ai/deepseek-coder-33B",
            memory_mb=18000,
            modality="code",
            specialties=["code", "debugging", "technical"]
        ),
        "mistral-7b": ExpertConfig(
            name="mistral-7b",
            model_id="mistralai/Mistral-7B-v0.3",
            memory_mb=4000,
            modality="text",
            specialties=["fast", "simple", "routing"]
        ),
        "mixtral-8x7b": ExpertConfig(
            name="mixtral-8x7b",
            model_id="mistralai/Mixtral-8x7B-v0.1",
            memory_mb=24000,
            modality="text",
            specialties=["instruction", "nuanced", "creative"]
        ),
        
        # Vision Experts
        "vita-1.5": ExpertConfig(
            name="vita-1.5",
            model_id="VITA-MLLM/VITA-1.5",
            memory_mb=28000,
            modality="vision",
            specialties=["vision-speech", "realtime"]
        ),
        "clip-vit": ExpertConfig(
            name="clip-vit",
            model_id="openai/clip-vit-large-patch14",
            memory_mb=2000,
            modality="vision",
            specialties=["similarity", "retrieval"]
        ),
        "sam-2": ExpertConfig(
            name="sam-2",
            model_id="facebook/sam2-hiera-large",
            memory_mb=8000,
            modality="vision",
            specialties=["segmentation", "detection"]
        ),
        
        # Audio Experts
        "whisper-v3": ExpertConfig(
            name="whisper-v3",
            model_id="openai/whisper-large-v3",
            memory_mb=3000,
            modality="audio",
            specialties=["speech-to-text", "multilingual"]
        ),
        "musicgen": ExpertConfig(
            name="musicgen",
            model_id="facebook/musicgen-large",
            memory_mb=12000,
            modality="audio",
            specialties=["music-generation", "creative"]
        ),
        
        # Code Experts
        "codellama-34b": ExpertConfig(
            name="codellama-34b",
            model_id="codellama/CodeLlama-34b-hf",
            memory_mb=18000,
            modality="code",
            specialties=["completion", "refactoring"]
        ),
        "starcoder-2": ExpertConfig(
            name="starcoder-2",
            model_id="bigcode/starcoder2-15b",
            memory_mb=12000,
            modality="code",
            specialties=["multi-language", "debugging"]
        ),
        
        # Math Experts
        "llemma-34b": ExpertConfig(
            name="llemma-34b",
            model_id="EleutherAI/llemma_34b",
            memory_mb=18000,
            modality="math",
            specialties=["reasoning", "theorem"]
        ),
        
        # Igbo Expert
        "igbo-language": ExpertConfig(
            name="igbo-language",
            model_id="agbara/igbo-expert-v1",
            memory_mb=8000,
            modality="text",
            specialties=["igbo", "culture", "translation"]
        )
    }
    
    def __init__(
        self,
        gpu_memory: int = 80 * 1024,  # 80GB default
        quantization: str = "4bit",
        cache_dir: str = "/tmp/agbara_cache",
        max_memory_utilization: float = 0.9
    ):
        """
        Initialize the Expert Manager.
        
        Args:
            gpu_memory: Total GPU memory in MB
            quantization: Quantization level
            cache_dir: Directory for model cache
            max_memory_utilization: Maximum GPU memory to use (0.0-1.0)
        """
        self.gpu_memory = gpu_memory
        self.quantization = quantization
        self.cache_dir = cache_dir
        self.max_memory_utilization = max_memory_utilization
        
        self.available_memory = int(gpu_memory * max_memory_utilization)
        self.used_memory = 0
        
        self.loaded_experts: Dict[str, Any] = {}
        self.expert_configs: Dict[str, ExpertConfig] = {}
        self.access_history: List[str] = []  # For LRU
        
        self._lock = threading.Lock()
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize expert configs
        for name, config in self.EXPERT_REGISTRY.items():
            self.expert_configs[name] = ExpertConfig(
                **{k: v for k, v in vars(config).items() 
                   if k not in ['state', 'loaded_at', 'error_message']}
            )
    
    def get_memory_usage(self) -> int:
        """Get current memory usage in MB."""
        return self.used_memory
    
    def get_available_memory(self) -> int:
        """Get available memory in MB."""
        return self.available_memory - self.used_memory
    
    def can_load(self, expert_name: str) -> bool:
        """Check if an expert can be loaded."""
        if expert_name not in self.expert_configs:
            return False
        
        config = self.expert_configs[expert_name]
        
        # Already loaded
        if config.state == ExpertState.LOADED:
            return True
        
        # Check memory
        memory_needed = config.memory_mb
        if self.get_available_memory() >= memory_needed:
            return True
        
        # Need to evict
        return self._can_evict_for(memory_needed)
    
    def _can_evict_for(self, memory_needed: int) -> bool:
        """Check if we can evict experts to make room."""
        available = self.get_available_memory()
        if available >= memory_needed:
            return True
        
        # Calculate potential savings from eviction
        # Only evict least recently used experts
        savings = 0
        for expert_name in self.access_history:
            if expert_name in self.loaded_experts:
                config = self.expert_configs[expert_name]
                savings += config.memory_mb
                if available + savings >= memory_needed:
                    return True
        
        return False
    
    def _evict_lru(self, memory_needed: int):
        """Evict least recently used experts to make room."""
        available = self.get_available_memory()
        needed = memory_needed - available
        
        evicted = []
        for expert_name in list(self.access_history):
            if needed <= 0:
                break
            
            if expert_name in self.loaded_experts:
                self.unload_expert(expert_name)
                config = self.expert_configs[expert_name]
                needed -= config.memory_mb
                evicted.append(expert_name)
        
        logger.info(f"Evicted experts: {evicted}")
        return evicted
    
    def load_expert(self, expert_name: str) -> bool:
        """
        Load an expert into GPU memory.
        
        Args:
            expert_name: Name of the expert to load
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if expert_name not in self.expert_configs:
                logger.error(f"Unknown expert: {expert_name}")
                return False
            
            config = self.expert_configs[expert_name]
            
            # Already loaded
            if config.state == ExpertState.LOADED:
                # Update access history
                if expert_name in self.access_history:
                    self.access_history.remove(expert_name)
                self.access_history.append(expert_name)
                return True
            
            # Check if we need to evict
            if not self.can_load(expert_name):
                logger.error(f"Cannot load {expert_name}: not enough memory")
                return False
            
            memory_needed = config.memory_mb
            if self.get_available_memory() < memory_needed:
                self._evict_lru(memory_needed)
            
            # Set loading state
            config.state = ExpertState.LOADING
            
            try:
                # Simulate model loading (in production, use vLLM/transformers)
                # For now, we'll create a placeholder
                self.loaded_experts[expert_name] = {
                    "config": config,
                    "model": None,  # Placeholder for actual model
                    "tokenizer": None  # Placeholder for tokenizer
                }
                
                # Update memory
                self.used_memory += memory_needed
                
                # Update state
                config.state = ExpertState.LOADED
                config.loaded_at = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
                
                # Update access history
                if expert_name in self.access_history:
                    self.access_history.remove(expert_name)
                self.access_history.append(expert_name)
                
                logger.info(f"Loaded expert: {expert_name}")
                return True
                
            except Exception as e:
                config.state = ExpertState.ERROR
                config.error_message = str(e)
                logger.error(f"Failed to load {expert_name}: {e}")
                return False
    
    def unload_expert(self, expert_name: str) -> bool:
        """
        Unload an expert from GPU memory.
        
        Args:
            expert_name: Name of the expert to unload
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if expert_name not in self.loaded_experts:
                return True  # Not loaded
            
            config = self.expert_configs[expert_name]
            
            try:
                # Free memory
                del self.loaded_experts[expert_name]
                self.used_memory -= config.memory_mb
                
                # Update state
                config.state = ExpertState.UNLOADED
                config.loaded_at = None
                
                # Remove from access history
                if expert_name in self.access_history:
                    self.access_history.remove(expert_name)
                
                logger.info(f"Unloaded expert: {expert_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unload {expert_name}: {e}")
                return False
    
    def get_loaded_experts(self) -> List[str]:
        """Get list of loaded expert names."""
        return list(self.loaded_experts.keys())
    
    def list_experts(self) -> List[Dict]:
        """List all available experts with their status."""
        experts = []
        for name, config in self.expert_configs.items():
            experts.append({
                "name": name,
                "modality": config.modality,
                "specialties": config.specialties,
                "memory_mb": config.memory_mb,
                "state": config.state.value,
                "loaded": name in self.loaded_experts
            })
        return experts
    
    def get_expert(self, expert_name: str) -> Optional[Any]:
        """Get a loaded expert instance."""
        return self.loaded_experts.get(expert_name)
    
    def warm_up(self, experts: List[str] = None):
        """
        Pre-load commonly used experts.
        
        Args:
            experts: List of expert names to warm up, or None for defaults
        """
        if experts is None:
            # Default warm-up: fast text expert and Igbo expert
            experts = ["mistral-7b", "igbo-language"]
        
        for expert_name in experts:
            if expert_name in self.expert_configs:
                self.load_expert(expert_name)
    
    def get_status(self) -> Dict:
        """Get detailed status of the expert manager."""
        return {
            "gpu_memory_total_mb": self.gpu_memory,
            "gpu_memory_available_mb": self.available_memory,
            "gpu_memory_used_mb": self.used_memory,
            "gpu_memory_free_mb": self.get_available_memory(),
            "utilization_percent": (self.used_memory / self.available_memory) * 100,
            "loaded_experts": len(self.loaded_experts),
            "total_experts": len(self.expert_configs),
            "quantization": self.quantization,
            "experts": self.list_experts()
        }
