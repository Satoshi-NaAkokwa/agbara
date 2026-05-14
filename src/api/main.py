"""
Agbara API Server - OpenAI-compatible FastAPI server.

Provides REST API endpoints for:
- Chat completions (streaming and non-streaming)
- Embeddings
- Models listing
- Health checks
"""

import os
import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import logging

# Import Agbara
from agbara import Agbara, __version__

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Agbara instance
agbara: Optional[Agbara] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Agbara on startup."""
    global agbara
    
    logger.info("Initializing Agbara...")
    
    agbara = Agbara(
        config_path=os.environ.get("AGBARA_CONFIG", None),
        gpu_memory=int(os.environ.get("AGBARA_GPU_MEMORY", 80 * 1024)),
        quantization=os.environ.get("AGBARA_QUANTIZATION", "4bit"),
        cache_dir=os.environ.get("AGBARA_CACHE_DIR", "/tmp/agbara_cache"),
        igbo_enabled=True
    )
    
    # Warm up commonly used experts
    agbara.expert_manager.warm_up(["mistral-7b", "igbo-language"])
    
    logger.info("Agbara initialized successfully")
    
    yield
    
    logger.info("Shutting down Agbara...")


# Create FastAPI app
app = FastAPI(
    title="Agbara API",
    description="The Self-Evolving Omni-Modal Intelligence System - OpenAI Compatible",
    version=__version__,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === OpenAI-Compatible Models ===

class ChatMessage(BaseModel):
    """Chat message."""
    role: str
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """Chat completion request."""
    model: str = "agbara"
    messages: List[ChatMessage]
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=1.0, ge=0, le=1)
    max_tokens: Optional[int] = None
    stream: bool = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: float = Field(default=0, ge=-2, le=2)
    frequency_penalty: float = Field(default=0, ge=-2, le=2)
    user: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    """Chat completion choice."""
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    """Token usage."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


class ModelInfo(BaseModel):
    """Model information."""
    id: str
    object: str = "model"
    created: int
    owned_by: str = "agbara-ai"


class ModelsResponse(BaseModel):
    """Models list response."""
    object: str = "list"
    data: List[ModelInfo]


# === API Key Authentication ===

API_KEYS = os.environ.get("AGBARA_API_KEYS", "").split(",")


def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify API key."""
    if not API_KEYS or API_KEYS == [""]:
        return True  # No auth required
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    if authorization.startswith("Bearer "):
        api_key = authorization[7:]
    else:
        api_key = authorization
    
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


# === Health Check ===

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": time.time()
    }


@app.get("/ready")
async def ready():
    """Readiness check endpoint."""
    if agbara is None:
        raise HTTPException(status_code=503, detail="Agbara not initialized")
    
    status = agbara.get_status()
    return {
        "ready": True,
        "status": status
    }


# === Models Endpoint ===

@app.get("/v1/models", response_model=ModelsResponse)
async def list_models(auth=Header(None)):
    """List available models."""
    verify_api_key(auth)
    
    models = [
        ModelInfo(id="agbara", created=int(time.time()), owned_by="agbara-ai"),
        ModelInfo(id="agbara-text", created=int(time.time()), owned_by="agbara-ai"),
        ModelInfo(id="agbara-code", created=int(time.time()), owned_by="agbara-ai"),
        ModelInfo(id="agbara-igbo", created=int(time.time()), owned_by="agbara-ai"),
        ModelInfo(id="agbara-vision", created=int(time.time()), owned_by="agbara-ai"),
    ]
    
    return ModelsResponse(data=models)


# === Chat Completions Endpoint ===

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    auth=Header(None)
):
    """Chat completions endpoint."""
    verify_api_key(auth)
    
    if agbara is None:
        raise HTTPException(status_code=503, detail="Agbara not initialized")
    
    # Extract messages
    messages = request.messages
    last_message = messages[-1] if messages else None
    
    if not last_message:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Build context
    context = [
        {"role": msg.role, "content": msg.content}
        for msg in messages[:-1]
    ]
    
    # Check for Igbo mode
    igbo_mode = "igbo" in request.model.lower()
    
    if request.stream:
        return StreamingResponse(
            stream_chat_completion(
                query=last_message.content,
                context=context,
                model=request.model,
                igbo_mode=igbo_mode
            ),
            media_type="text/event-stream"
        )
    
    # Non-streaming response
    response = agbara.process(
        query=last_message.content,
        stream=False,
        context=context,
        igbo_mode=igbo_mode
    )
    
    # Build response
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    
    return ChatCompletionResponse(
        id=completion_id,
        created=int(time.time()),
        model=request.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=response
                ),
                finish_reason="stop"
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=len(last_message.content.split()),
            completion_tokens=len(response.split()) if isinstance(response, str) else 0,
            total_tokens=len(last_message.content.split()) + len(response.split()) if isinstance(response, str) else 0
        )
    )


async def stream_chat_completion(
    query: str,
    context: List[Dict],
    model: str,
    igbo_mode: bool
):
    """Stream chat completion chunks."""
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    
    async for chunk in agbara.process_async(
        query=query,
        stream=True,
        context=context,
        igbo_mode=igbo_mode
    ):
        import json
        
        chunk_data = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": chunk.get("chunk", "")},
                    "finish_reason": None if not chunk.get("is_final") else "stop"
                }
            ]
        }
        
        yield f"data: {json.dumps(chunk_data)}\n\n"
    
    yield "data: [DONE]\n\n"


# === Completions Endpoint (Legacy) ===

class CompletionRequest(BaseModel):
    """Legacy completion request."""
    model: str = "agbara"
    prompt: str
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    stream: bool = False


@app.post("/v1/completions")
async def completions(
    request: CompletionRequest,
    auth=Header(None)
):
    """Legacy completions endpoint."""
    verify_api_key(auth)
    
    if agbara is None:
        raise HTTPException(status_code=503, detail="Agbara not initialized")
    
    response = agbara.process(
        query=request.prompt,
        stream=False
    )
    
    return {
        "id": f"cmpl-{uuid.uuid4().hex[:24]}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "text": response,
                "index": 0,
                "finish_reason": "stop"
            }
        ]
    }


# === Embeddings Endpoint ===

class EmbeddingRequest(BaseModel):
    """Embedding request."""
    model: str = "agbara-embedding"
    input: Union[str, List[str]]


@app.post("/v1/embeddings")
async def embeddings(
    request: EmbeddingRequest,
    auth=Header(None)
):
    """Embeddings endpoint."""
    verify_api_key(auth)
    
    # Placeholder - in production, use actual embedding model
    import hashlib
    import json
    
    texts = [request.input] if isinstance(request.input, str) else request.input
    
    embeddings = []
    for i, text in enumerate(texts):
        # Generate deterministic placeholder embedding
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = [float(b) / 255.0 for b in hash_bytes[:128]]
        
        embeddings.append({
            "object": "embedding",
            "index": i,
            "embedding": embedding
        })
    
    return {
        "object": "list",
        "data": embeddings,
        "model": request.model,
        "usage": {
            "prompt_tokens": sum(len(t.split()) for t in texts),
            "total_tokens": sum(len(t.split()) for t in texts)
        }
    }


# === Agbara-Specific Endpoints ===

@app.get("/v1/experts")
async def list_experts(auth=Header(None)):
    """List available experts."""
    verify_api_key(auth)
    
    if agbara is None:
        raise HTTPException(status_code=503, detail="Agbara not initialized")
    
    return {
        "experts": agbara.list_experts()
    }


@app.post("/v1/experts/{expert_name}/load")
async def load_expert(expert_name: str, auth=Header(None)):
    """Load a specific expert."""
    verify_api_key(auth)
    
    if agbara is None:
        raise HTTPException(status_code=503, detail="Agbara not initialized")
    
    success = agbara.load_expert(expert_name)
    
    if success:
        return {"status": "loaded", "expert": expert_name}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to load expert: {expert_name}")


@app.post("/v1/experts/{expert_name}/unload")
async def unload_expert(expert_name: str, auth=Header(None)):
    """Unload a specific expert."""
    verify_api_key(auth)
    
    if agbara is None:
        raise HTTPException(status_code=503, detail="Agbara not initialized")
    
    success = agbara.unload_expert(expert_name)
    
    return {"status": "unloaded" if success else "not_loaded", "expert": expert_name}


@app.get("/v1/status")
async def get_status(auth=Header(None)):
    """Get Agbara system status."""
    verify_api_key(auth)
    
    if agbara is None:
        raise HTTPException(status_code=503, detail="Agbara not initialized")
    
    return agbara.get_status()


# === Igbo-Specific Endpoints ===

@app.get("/v1/igbo/proverb")
async def get_igbo_proverb(category: Optional[str] = None, auth=Header(None)):
    """Get an Igbo proverb."""
    verify_api_key(auth)
    
    if agbara is None or not agbara.igbo_expert:
        raise HTTPException(status_code=503, detail="Igbo expert not available")
    
    proverb = agbara.igbo_expert.get_proverb_for_context(category or "")
    
    if proverb:
        return {
            "igbo": proverb.igbo,
            "english": proverb.english,
            "meaning": proverb.meaning,
            "context": proverb.context,
            "category": proverb.category
        }
    
    return {"error": "No proverb found"}


@app.post("/v1/igbo/translate")
async def translate_igbo(text: str, direction: str = "igbo-to-english", auth=Header(None)):
    """Translate between Igbo and English."""
    verify_api_key(auth)
    
    if agbara is None or not agbara.igbo_expert:
        raise HTTPException(status_code=503, detail="Igbo expert not available")
    
    if direction == "igbo-to-english":
        translation = agbara.igbo_expert.translate_igbo_to_english(text)
    else:
        # For English to Igbo, use the main process
        translation = agbara.process(f"Translate to Igbo: {text}", igbo_mode=True)
    
    return {
        "original": text,
        "translation": translation,
        "direction": direction
    }


# === Prometheus Metrics ===

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if agbara is None:
        return "# Agbara not initialized"
    
    status = agbara.get_status()
    
    metrics_text = f"""
# HELP agbara_gpu_memory_used_mb GPU memory used in MB
# TYPE agbara_gpu_memory_used_mb gauge
agbara_gpu_memory_used_mb {status['gpu_memory_used']}

# HELP agbara_gpu_memory_total_mb Total GPU memory in MB
# TYPE agbara_gpu_memory_total_mb gauge
agbara_gpu_memory_total_mb {status['gpu_memory_total']}

# HELP agbara_cache_size Number of cached entries
# TYPE agbara_cache_size gauge
agbara_cache_size {status['cache_size']}

# HELP agbara_experts_loaded Number of loaded experts
# TYPE agbara_experts_loaded gauge
agbara_experts_loaded {status['experts_loaded']}

# HELP agbara_igbo_enabled Whether Igbo expert is enabled
# TYPE agbara_igbo_enabled gauge
agbara_igbo_enabled {1 if status['igbo_enabled'] else 0}
"""
    
    return metrics_text


# === Main Entry Point ===

if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("AGBARA_HOST", "0.0.0.0")
    port = int(os.environ.get("AGBARA_PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        workers=1
    )
