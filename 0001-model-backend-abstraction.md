# ADR-0001: Model Backend Abstraction

## Status
Accepted

## Date
2024-12-03

## Context

Veyra needs to support multiple LLM providers (OpenAI, Anthropic, local models via Ollama) while maintaining:

1. **Consistent interface** for the core system regardless of backend
2. **Auditability** of all model interactions
3. **Testability** without requiring API keys or network access
4. **Extensibility** for future providers without core changes

The challenge is balancing flexibility with the constraint that different providers have different APIs, capabilities, rate limits, and failure modes.

## Decision

We will implement a **Backend Abstraction Layer** using:

1. **Abstract Base Class** (`BaseModelBackend`) defining the contract:
   ```python
   class BaseModelBackend(ABC):
       name: str
       
       @abstractmethod
       async def generate(self, prompt: str, **kwargs) -> ModelResponse:
           pass
       
       @abstractmethod
       async def health_check(self) -> bool:
           pass
   ```

2. **Standardized Response Object** (`ModelResponse`) that normalizes provider responses:
   ```python
   @dataclass
   class ModelResponse:
       content: str
       model: str
       backend: str
       latency_ms: float
       prompt_tokens: int
       completion_tokens: int
       request_id: Optional[str]
   ```

3. **Registry Pattern** for backend discovery:
   ```python
   def get_backend(name: str, **kwargs) -> BaseModelBackend:
       backends = {"mock": MockBackend, "openai": OpenAIBackend, ...}
       return backends[name](**kwargs)
   ```

4. **Mock Backend** as first-class citizen for testing and demos

## Consequences

### Positive
- Core system decoupled from provider specifics
- Easy to add new backends (implement 2 methods)
- Mock backend enables zero-cost testing and demos
- Consistent audit logging regardless of backend
- Provider failures isolated from core logic

### Negative
- Some provider-specific features may be unavailable through abstraction
- Additional indirection layer
- Must maintain backend implementations as providers evolve

### Neutral
- Configuration determines backend at runtime
- Each backend responsible for its own error handling

## Alternatives Considered

1. **Direct provider SDK usage**: Rejected due to tight coupling and test difficulty
2. **LangChain/LiteLLM wrapper**: Rejected due to dependency bloat and control loss
3. **Plugin system**: Deferred—current registry pattern is simpler and sufficient

## References
- `src/veyra/models/base.py` - Base class implementation
- `src/veyra/models/registry.py` - Backend registry
- `src/veyra/models/mock.py` - Reference implementation
