# YouTube Summarizer - Future Enhancements Roadmap

This document outlines potential future enhancements for the YouTube Summarizer, focusing on backend flexibility and broader hardware compatibility.

## Current State

**Version:** 0.1.0
**Backend:** Ollama (local LLM inference)
**GPU Support:** NVIDIA CUDA only
**Performance:** 28.7s for 71-minute video (RTX 5080 + llama3.1:8b)

The tool currently works excellently with NVIDIA GPUs but has opportunities for expansion to support more users and use cases.

---

## Path 1: AMD GPU Support (ROCm Backend)

### Overview

Extend hardware compatibility to AMD GPUs using ROCm (AMD's CUDA equivalent).

### Feasibility: **8/10** (HIGH)

**What Would Work:**
- Modern AMD GPUs: RX 6000/7000 series, Radeon VII
- ROCm is mature enough for LLM inference
- Ollama already has `ollama-rocm` package available
- Linux (especially Arch/CachyOS) has excellent ROCm support
- Same Ollama API - just swap the backend package

### Technical Requirements

**Package Installation:**
```bash
# AMD GPU support requires:
yay -S ollama-rocm rocm-hip-sdk rocm-opencl-runtime

# Environment variables may be needed:
export HSA_OVERRIDE_GFX_VERSION=<gpu_version>
export ROCR_VISIBLE_DEVICES=0
```

**GPU Compatibility Matrix:**

| GPU Series | ROCm Support | Expected Performance |
|------------|--------------|---------------------|
| RDNA3 (RX 7000) | ✅ Excellent | Similar to NVIDIA equivalent |
| RDNA2 (RX 6000) | ✅ Good | ~80-90% of NVIDIA equivalent |
| RDNA1 (RX 5000) | ⚠️ Limited | May work with workarounds |
| GCN (older) | ❌ Poor | Not recommended |

### Challenges

1. **Setup Complexity**
   - ROCm installation more complex than CUDA
   - GPU-specific environment variables often needed
   - Driver compatibility issues more common

2. **Performance Variability**
   - Sometimes slower than NVIDIA equivalent
   - Optimization less mature for LLM workloads
   - Memory bandwidth can be limiting factor

3. **Debugging & Support**
   - Smaller community than CUDA
   - Less documentation for edge cases
   - More platform-specific issues

### Implementation Approach

**Auto-detection logic:**
```python
# config.py
def detect_gpu_backend():
    """Auto-detect available GPU backend."""
    if has_nvidia_gpu():
        return "cuda"
    elif has_amd_gpu():
        return "rocm"
    else:
        return "cpu"

# Recommend appropriate package:
backend = detect_gpu_backend()
print(f"Recommended: ollama-{backend}")
```

**Installation guidance:**
- Add GPU detection to CLI
- Display backend-specific installation instructions
- Provide troubleshooting guide for ROCm issues

### Estimated Implementation Effort

**Time:** 2-3 hours

**Tasks:**
- GPU detection utility
- Backend recommendation system
- Documentation updates (installation, troubleshooting)
- Testing on AMD hardware

**Priority:** Medium (smaller user base than NVIDIA)

---

## Path 2: OpenAI API Integration (Cloud Backend)

### Overview

Add support for OpenAI's API (starting with gpt-4o-mini) as an alternative backend, enabling use without local GPU.

### Feasibility: **9/10** (VERY HIGH)

**Why This Is Attractive:**

1. **Minimal Cost** - essentially free for typical usage
2. **No GPU Required** - works on any laptop/desktop
3. **Super Fast** - 2-5 seconds regardless of video length
4. **Excellent Quality** - often better than llama3.1:70b
5. **Universal Compatibility** - Mac, Windows, Linux, WSL

### Cost Analysis

**gpt-4o-mini Pricing (2025):**
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Real-World Examples:**

| Video Length | Input Tokens | Output Tokens | Total Cost |
|--------------|--------------|---------------|------------|
| 3 min (Rick Astley) | 522 | ~500 | $0.0004 |
| 9 min (TED Talk) | 2,276 | ~500 | $0.0007 |
| 71 min (long) | 19,722 | ~1,977 | $0.004 |

**Monthly Usage (60 videos, mixed lengths):**
- Estimated: ~$0.08/month
- Practically free compared to electricity costs

### Pros and Cons

**Advantages:**
- ✅ No GPU setup required
- ✅ Works on any hardware (even Raspberry Pi)
- ✅ Extremely fast (2-5s for any video)
- ✅ High quality summaries
- ✅ Scales to very long videos without chunking
- ✅ No local storage for models (saves ~5GB)

**Disadvantages:**
- ⚠️ **Privacy**: Transcript sent to OpenAI
- ⚠️ Requires internet connection
- ⚠️ API key management (security consideration)
- ⚠️ Subject to rate limits (generous but present)
- ⚠️ Ongoing cost (though minimal)

### Implementation Approach

**Architecture - Backend Abstraction:**

```python
# New backend system:
class SummarizerBackend(ABC):
    @abstractmethod
    def summarize(self, transcript, metadata) -> str:
        pass

class OllamaBackend(SummarizerBackend):
    # Existing implementation
    pass

class OpenAIBackend(SummarizerBackend):
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def summarize(self, transcript, metadata):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": build_prompt(transcript, metadata)
            }],
            max_tokens=calculate_dynamic_limit(transcript)
        )
        return response.choices[0].message.content
```

**User Experience:**

```bash
# Auto-detection with prompt:
$ yts summarize VIDEO_URL
> No GPU detected. Options:
> 1. OpenAI API (fast, ~$0.004/video, requires API key)
> 2. Ollama CPU mode (slow, free, local)
> 3. Set up GPU support (fast, free, local, requires setup)
> Choice [1]:

# Explicit backend selection:
$ yts summarize VIDEO_URL --backend openai
$ yts summarize VIDEO_URL --backend ollama

# Configuration:
$ export YTS_BACKEND=openai
$ export YTS_OPENAI_API_KEY=sk-...
# Or store in ~/.config/youtube-summarizer/config.yaml
```

**Smart Defaults:**

```python
# Priority order for backend selection:
1. User explicit choice (--backend flag)
2. Environment variable (YTS_BACKEND)
3. GPU available? → Use Ollama
4. OpenAI key configured? → Use OpenAI
5. Nothing available? → Prompt user
```

### Security Considerations

**API Key Storage:**
- Use OS keyring integration (keyring library)
- Never commit keys to git
- Environment variables as fallback
- Warn users about .env file security

**Privacy Options:**
- Add `--local-only` flag to prevent cloud backends
- Clear warning when using cloud services
- Option to review transcript before sending

### Estimated Implementation Effort

**Time:** 4-6 hours

**Tasks:**
- Add OpenAI SDK dependency
- Create backend abstraction layer
- Implement OpenAIBackend class
- Backend selection/auto-detection logic
- API key management (keyring integration)
- Update CLI for `--backend` flag
- Documentation updates
- Error handling for API failures

**Priority:** High (broadest user impact)

---

## Backend Comparison Table

| Feature | Ollama (Local) | OpenAI API |
|---------|----------------|------------|
| **Privacy** | ✅ 100% local processing | ❌ Cloud-based (data sent to OpenAI) |
| **Cost** | ✅ Free (electricity ~$0.00016/video) | ✅ Nearly free (~$0.004/video) |
| **Speed (GPU)** | ✅ 5-30 seconds | ✅✅ 2-5 seconds |
| **Speed (CPU)** | ❌ 1-10 minutes | ✅✅ 2-5 seconds |
| **Setup** | ⚠️ GPU drivers, model downloads | ✅ Just API key |
| **Quality (8b)** | ✅ Good | - |
| **Quality (70b)** | ✅✅ Excellent | - |
| **Quality (gpt-4o-mini)** | - | ✅✅ Excellent |
| **Offline Support** | ✅ Works offline | ❌ Requires internet |
| **Hardware Requirements** | ⚠️ 16GB+ RAM, GPU preferred | ✅ Any hardware |
| **Model Storage** | ❌ 5-40GB per model | ✅ None |
| **Sensitive Content** | ✅ Safe for proprietary videos | ⚠️ OpenAI's data policy applies |

---

## Recommendations

### Phase 1: OpenAI API Integration (Recommended First)

**Why prioritize this:**

1. **Broader User Base**
   - Works for users without GPUs
   - Works on Mac/Windows without hassle
   - Fallback when GPU issues arise

2. **Lower Barrier to Entry**
   - $5 OpenAI credit = 1,000+ summaries
   - No driver installation
   - Works in 5 minutes

3. **Better User Experience**
   - Faster than CPU-only Ollama
   - More reliable (no GPU driver issues)
   - Easier troubleshooting

**Use Cases:**
- Quick testing/evaluation
- Users without NVIDIA GPUs
- Laptop/portable usage
- When GPU isn't available (gaming, rendering, etc.)

### Phase 2: AMD GPU Support (Lower Priority)

**When to implement:**

1. User requests from AMD GPU owners
2. Personal need (if you get an AMD GPU)
3. After OpenAI backend is stable

**Why lower priority:**
- NVIDIA dominates GPU market (~80%)
- More complex setup and support
- ROCm ecosystem still maturing
- Smaller potential user base

### Hybrid Strategy (Best of Both Worlds)

**Recommended approach:**

```
Default behavior:
├─ GPU detected (NVIDIA) → Ollama CUDA ✅
├─ GPU detected (AMD) → Ollama ROCm (if implemented)
├─ OpenAI key set → OpenAI API ✅
└─ None → Prompt user to choose
```

**User benefits:**
- Privacy-conscious users: Use Ollama
- Convenience-focused users: Use OpenAI
- Cost-conscious users: Use Ollama with GPU
- No-GPU users: Use OpenAI or CPU-mode Ollama

---

## Future Considerations

### Additional Backends

**Anthropic Claude (claude-3-haiku):**
- Similar to OpenAI approach
- Excellent quality, fast responses
- Competitive pricing

**Groq (llama3-8b-8192):**
- Free tier available
- Extremely fast (often <1s)
- Good quality

**Google Gemini (gemini-1.5-flash):**
- Very competitive pricing
- Good quality for summaries
- Large context window (1M tokens)

### Model Selection Per Backend

```bash
# Ollama backend:
yts summarize URL --backend ollama --model llama3.1:70b

# OpenAI backend:
yts summarize URL --backend openai --model gpt-4o-mini
yts summarize URL --backend openai --model gpt-4o  # Premium
```

### Quality vs Cost Tradeoffs

Allow users to select quality tier:
- `--quality fast`: gpt-4o-mini / llama3.1:8b
- `--quality balanced`: gpt-4o / llama3.1:70b
- `--quality premium`: claude-opus / gpt-4-turbo

---

## Conclusion

This roadmap outlines two primary enhancement paths:

1. **OpenAI API Integration** (High priority, 4-6 hours)
   - Broadest user impact
   - Easiest to implement
   - Provides fallback option

2. **AMD GPU Support** (Medium priority, 2-3 hours)
   - Valuable for AMD users
   - Smaller audience
   - More complex support

**Next Steps:**
- Community feedback on priorities
- Technical proof-of-concept for OpenAI backend
- User research on AMD GPU demand

The tool's modular architecture makes both paths feasible without disrupting existing functionality.

---

*Last Updated: 2025-10-25*
*Current Version: 0.1.0*
