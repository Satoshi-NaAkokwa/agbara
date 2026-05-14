"""
Expert Router - Intelligent routing to the best expert(s) for each query.
"""

import asyncio
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np
from enum import Enum


class Modality(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    MATH = "math"
    IGBO = "igbo"


@dataclass
class ExpertAssignment:
    """Assignment of a query to an expert."""
    expert_name: str
    weight: float
    modality: Modality
    estimated_tokens: int
    estimated_latency_ms: int


class ExpertRouter:
    """
    Intelligent expert router that directs queries to the optimal expert(s).
    
    Features:
    - Modality detection (text, image, audio, video, code, math, igbo)
    - Complexity assessment
    - Domain classification
    - Load balancing across experts
    - Performance tracking
    - Igbo language detection and routing
    """
    
    # Expert configurations
    TEXT_EXPERTS = {
        "llama4-70b": {
            "weight": 1.0,
            "specialties": ["reasoning", "general", "long-context"],
            "memory_mb": 35000,
            "latency_ms": 500
        },
        "qwen3-72b": {
            "weight": 1.0,
            "specialties": ["multilingual", "scientific", "math"],
            "memory_mb": 36000,
            "latency_ms": 550
        },
        "deepseek-coder": {
            "weight": 0.9,
            "specialties": ["code", "debugging", "technical"],
            "memory_mb": 18000,
            "latency_ms": 400
        },
        "mistral-7b": {
            "weight": 0.7,
            "specialties": ["fast", "simple", "routing"],
            "memory_mb": 4000,
            "latency_ms": 150
        },
        "mixtral-8x7b": {
            "weight": 0.95,
            "specialties": ["instruction", "nuanced", "creative"],
            "memory_mb": 24000,
            "latency_ms": 350
        }
    }
    
    VISION_EXPERTS = {
        "vita-1.5": {
            "weight": 1.0,
            "specialties": ["vision-speech", "realtime", "gpt4o-level"],
            "memory_mb": 28000,
            "latency_ms": 300
        },
        "clip-vit": {
            "weight": 0.6,
            "specialties": ["similarity", "retrieval", "classification"],
            "memory_mb": 2000,
            "latency_ms": 100
        },
        "sam-2": {
            "weight": 0.8,
            "specialties": ["segmentation", "detection", "localization"],
            "memory_mb": 8000,
            "latency_ms": 250
        },
        "blip-3": {
            "weight": 0.7,
            "specialties": ["captioning", "vqa", "understanding"],
            "memory_mb": 6000,
            "latency_ms": 200
        }
    }
    
    AUDIO_EXPERTS = {
        "whisper-v3": {
            "weight": 1.0,
            "specialties": ["speech-to-text", "multilingual", "transcription"],
            "memory_mb": 3000,
            "latency_ms": 200
        },
        "musicgen": {
            "weight": 0.8,
            "specialties": ["music-generation", "creative", "composition"],
            "memory_mb": 12000,
            "latency_ms": 500
        },
        "seamless-m4t": {
            "weight": 0.9,
            "specialties": ["translation", "universal", "multimodal"],
            "memory_mb": 15000,
            "latency_ms": 400
        }
    }
    
    CODE_EXPERTS = {
        "codellama-34b": {
            "weight": 1.0,
            "specialties": ["completion", "refactoring", "documentation"],
            "memory_mb": 18000,
            "latency_ms": 350
        },
        "starcoder-2": {
            "weight": 0.9,
            "specialties": ["multi-language", "debugging", "generation"],
            "memory_mb": 20000,
            "latency_ms": 400
        },
        "wizard-coder": {
            "weight": 0.85,
            "specialties": ["problem-solving", "instruction", "complex"],
            "memory_mb": 16000,
            "latency_ms": 380
        }
    }
    
    MATH_EXPERTS = {
        "llemma-34b": {
            "weight": 1.0,
            "specialties": ["reasoning", "theorem", "proof"],
            "memory_mb": 18000,
            "latency_ms": 400
        },
        "mathgemma": {
            "weight": 0.95,
            "specialties": ["advanced", "physics", "simulation"],
            "memory_mb": 15000,
            "latency_ms": 350
        }
    }
    
    IGBO_EXPERT = {
        "igbo-language": {
            "weight": 1.0,
            "specialties": ["igbo", "culture", "translation", "proverbs"],
            "memory_mb": 8000,
            "latency_ms": 250
        }
    }
    
    def __init__(self, expert_manager, cache_manager):
        self.expert_manager = expert_manager
        self.cache_manager = cache_manager
        self.performance_history: Dict[str, List[float]] = {}
        
    def detect_modality(self, query: str, input_data: Any = None) -> Modality:
        """Detect the modality of the input."""
        # Check if input_data is provided
        if input_data is not None:
            if isinstance(input_data, np.ndarray):
                if len(input_data.shape) == 3:
                    return Modality.IMAGE
                elif len(input_data.shape) == 4:
                    return Modality.VIDEO
            elif isinstance(input_data, bytes):
                return Modality.AUDIO
        
        # Check for Igbo language markers
        igbo_markers = [
            "ndewo", "kedu", "biko", "daalụ", "nne", "nna", "ụmụ",
            "chi", "ndichie", "ala", "ife", "mmiri", "oku", "ifele",
            "jụọ", "gwara", "kwuru", "dee", "gụọ", "bịa", "ga"
        ]
        query_lower = query.lower()
        if any(marker in query_lower for marker in igbo_markers):
            return Modality.IGBO
        
        # Check for code markers
        code_markers = [
            "def ", "class ", "import ", "function", "code", "python",
            "javascript", "typescript", "java", "c++", "rust", "golang",
            "debug", "error", "exception", "stack trace", "```"
        ]
        if any(marker in query_lower for marker in code_markers):
            return Modality.CODE
        
        # Check for math markers
        math_markers = [
            "solve", "equation", "calculate", "prove", "theorem",
            "integral", "derivative", "matrix", "vector", "function f",
            "x^2", "log(", "sin(", "cos(", "∑", "∫", "π"
        ]
        if any(marker in query_lower for marker in math_markers):
            return Modality.MATH
        
        return Modality.TEXT
    
    def assess_complexity(self, query: str) -> float:
        """Assess the complexity of a query (0.0 to 1.0)."""
        complexity = 0.0
        
        # Length factor
        word_count = len(query.split())
        if word_count > 100:
            complexity += 0.2
        elif word_count > 50:
            complexity += 0.1
        
        # Technical depth indicators
        technical_markers = [
            "explain", "analyze", "compare", "synthesize", "design",
            "architect", "optimize", "refactor", "implement", "create"
        ]
        query_lower = query.lower()
        complexity += sum(0.1 for m in technical_markers if m in query_lower)
        
        # Multi-step indicators
        multi_step = ["first", "then", "finally", "step by step", "also", "additionally"]
        complexity += sum(0.05 for m in multi_step if m in query_lower)
        
        return min(complexity, 1.0)
    
    def classify_domain(self, query: str) -> List[str]:
        """Classify the domain(s) of a query."""
        domains = []
        query_lower = query.lower()
        
        domain_keywords = {
            "programming": ["code", "function", "class", "api", "debug", "compile"],
            "science": ["research", "experiment", "hypothesis", "theory", "study"],
            "mathematics": ["calculate", "solve", "equation", "proof", "theorem"],
            "language": ["translate", "grammar", "write", "essay", "story"],
            "igbo": ["igbo", "ndigbo", "omenala", "omenani", "ala igbo"],
            "business": ["market", "strategy", "finance", "invest", "profit"],
            "creative": ["create", "design", "imagine", "story", "art"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                domains.append(domain)
        
        return domains if domains else ["general"]
    
    def select_experts(
        self,
        modality: Modality,
        complexity: float,
        domains: List[str]
    ) -> List[ExpertAssignment]:
        """Select the best expert(s) for the query."""
        assignments = []
        
        # Get expert pool based on modality
        if modality == Modality.TEXT:
            expert_pool = self.TEXT_EXPERTS
        elif modality == Modality.VISION or modality == Modality.IMAGE:
            expert_pool = self.VISION_EXPERTS
        elif modality == Modality.AUDIO:
            expert_pool = self.AUDIO_EXPERTS
        elif modality == Modality.CODE:
            expert_pool = self.CODE_EXPERTS
        elif modality == Modality.MATH:
            expert_pool = self.MATH_EXPERTS
        elif modality == Modality.IGBO:
            expert_pool = self.IGBO_EXPERT
        else:
            expert_pool = self.TEXT_EXPERTS
        
        # For high complexity, use larger models
        for expert_name, config in expert_pool.items():
            # Adjust weight based on complexity
            adjusted_weight = config["weight"]
            if complexity > 0.7:
                # Prefer larger models for complex queries
                if config["memory_mb"] > 20000:
                    adjusted_weight *= 1.2
            elif complexity < 0.3:
                # Prefer smaller models for simple queries
                if config["memory_mb"] < 10000:
                    adjusted_weight *= 1.3
            
            # Check domain match
            specialty_match = any(
                spec in domains or spec in ["general", "fast", "reasoning"]
                for spec in config["specialties"]
            )
            if specialty_match:
                adjusted_weight *= 1.1
            
            assignments.append(ExpertAssignment(
                expert_name=expert_name,
                weight=min(adjusted_weight, 2.0),
                modality=modality,
                estimated_tokens=500,  # Placeholder
                estimated_latency_ms=config["latency_ms"]
            ))
        
        # Sort by weight and return top experts
        assignments.sort(key=lambda x: x.weight, reverse=True)
        
        # For complex queries, return multiple experts for fusion
        if complexity > 0.7:
            return assignments[:2]
        else:
            return assignments[:1]
    
    def route(
        self,
        query: str,
        modality: str = None,
        igbo_mode: bool = False
    ) -> List[ExpertAssignment]:
        """
        Route a query to the optimal expert(s).
        
        Args:
            query: Input query
            modality: Forced modality (optional)
            igbo_mode: Force Igbo language mode
            
        Returns:
            List of expert assignments
        """
        # Detect or use forced modality
        if igbo_mode:
            detected_modality = Modality.IGBO
        elif modality:
            detected_modality = Modality(modality)
        else:
            detected_modality = self.detect_modality(query)
        
        # Assess complexity
        complexity = self.assess_complexity(query)
        
        # Classify domain
        domains = self.classify_domain(query)
        
        # Select experts
        assignments = self.select_experts(detected_modality, complexity, domains)
        
        return assignments
    
    async def route_async(
        self,
        query: str,
        modality: str = None,
        igbo_mode: bool = False
    ) -> List[ExpertAssignment]:
        """Async version of route."""
        return self.route(query, modality, igbo_mode)
    
    def update_performance(self, expert_name: str, latency_ms: float, quality_score: float):
        """Update performance history for an expert."""
        if expert_name not in self.performance_history:
            self.performance_history[expert_name] = []
        self.performance_history[expert_name].append({
            "latency_ms": latency_ms,
            "quality": quality_score
        })
    
    def get_expert_performance(self, expert_name: str) -> Dict:
        """Get performance stats for an expert."""
        history = self.performance_history.get(expert_name, [])
        if not history:
            return {"avg_latency_ms": 0, "avg_quality": 0, "samples": 0}
        
        return {
            "avg_latency_ms": sum(h["latency_ms"] for h in history) / len(history),
            "avg_quality": sum(h["quality"] for h in history) / len(history),
            "samples": len(history)
        }
