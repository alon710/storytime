# StoryTime Project Rules for Claude

## 🔄 IMPORTANT: Keep This File Updated

Always update this CLAUDE.md whenever project structure, patterns, or dependencies change. This ensures the guidance remains accurate for future development.

## 📚 Project Overview

StoryTime is an AI-powered storytelling system built with LangChain and multiple AI models (Gemini, GPT, etc.). The system runs a main conversational agent that orchestrates four specialized tools, each with its own model, to create personalized children's books with custom illustrations.

### ✨ Core Features

- **Conversational flow** to collect child's details (name, age, gender, challenge, reference images)
- **Tool-based architecture**: seed image generator, narrator, illustrator, storage
- **Support for different AI models** per tool (Gemini, GPT, others)
- **Consistent illustration generation** across story pages
- **Organized per-session storage** of texts and images

## 🏗️ Architecture & Project Structure

```
app.py              # Streamlit chat-based UI entry point
app/
├── agent.py        # Main conversational agent with LangChain orchestration
├── main.py         # Legacy orchestration (kept for reference)
├── settings.py     # Multi-model configuration and environment settings
├── database/
│   ├── models.py   # SQLAlchemy models for sessions, chat history, content
│   └── session_manager.py # Database operations and session management
└── tools/
    ├── base.py     # LangChain-compatible base class with structured logging
    ├── seed.py     # Generates seed images for characters (child, mom, doll, etc.)
    ├── narrator.py # Generates book name, page titles, story texts, and scene descriptions
    ├── illustrator.py # Generates page illustrations using prompts, seed images, and past pages
    └── storage.py  # Persists story text and illustrations to session directories
```

## 🛠️ Dependencies & Technologies

### Core
- **Python 3.12+** - Latest Python runtime
- **LangChain** - Agent orchestration and tool integration
- **Google GenAI (Gemini) / OpenAI GPT** - Model flexibility
- **SQLAlchemy** - Database ORM with async support
- **SQLite** - Session and chat storage
- **Pydantic** - Data validation & config
- **Pillow** - Image processing
- **structlog** - Structured logging
- **Streamlit** - Chat-based web UI framework

### Development
- **uv** - Package management
- **pyproject.toml** - Project config
- **pytest** (+ coverage, asyncio, mocking) - Testing framework
- **Ruff** - Linting & formatting
- **ty** - Type checker

## 🤖 Agent & Tool Design

### Main Conversational Agent (`agent.py`)
- **LangChain-based conversational flow** with natural language processing
- **Session-aware context** - remembers previous conversations
- **Smart information extraction** - automatically parses user responses
- **Ensures all required details are collected:**
  - Child's name, age, gender
  - Challenge/theme
  - Reference images (optional)
- **Tool orchestration** when all information is collected

### 🛠️ Tool Responsibilities

#### `seed.py`
- Generates seed character images
- Supports multiple entities (child, family, toys, etc.)
- Configurable AI backend (Gemini/GPT/custom)

#### `narrator.py`
- **Generates storybook metadata and content:**
  - Book title
  - Page titles
  - Page text
  - Scene descriptions for illustrations
- Runs on its own AI model (fast JSON-capable model recommended)

#### `illustrator.py`
- Creates illustrations per page
- Uses seed images + previously generated pages for consistency
- Configurable to higher-quality image models

#### `storage.py`
- Persists texts and images
- Session-based directory structure

## ⚙️ Multi-Model Configuration

Each tool (and the main agent) can be bound to a custom AI model:

```python
class Settings(BaseSettings):
    main_agent_model: str = "gpt-4o-mini"
    seed_model: str = "gemini-2.0-flash-exp"
    narrator_model: str = "gemini-1.5-pro"
    illustrator_model: str = "gemini-2.5-flash-image-preview"
    storage_backend: str = "local"
```

### 📋 Guidelines
- **Main Agent**: Conversational, dialog-heavy → GPT recommended
- **Seed Tool**: Fast, consistent image generation → Gemini Flash Exp
- **Narrator Tool**: Strong text and structure → Gemini Pro or GPT
- **Illustrator Tool**: High-quality visuals → Gemini Image Preview
- **Storage Tool**: Local or cloud backend (non-AI)

### 🎯 Model Selection Strategy
- **Performance-first** → GPT for main + Gemini flash for tools
- **Quality-first** → Pro/Gemini high-quality image + GPT-4 for narrator
- **Cost optimization** → Use lightweight models for seed/narrator, heavier for illustrator

## 📝 Coding Conventions

### Type Hints
- **Type hints mandatory**
- **Always use built-in `list` and `dict` for type hinting**
- **Use pipe operator for union types**

✅ `list[str]`
✅ `dict[str, int]`
✅ `str | None` (instead of `Optional[str]`)
✅ `list[Image] | None`
❌ `List[str]`
❌ `Dict[str, int]`
❌ `Optional[str]`

### Import Style
- **Always use absolute imports**
- **Never use relative imports**

✅ `from app.tools.base import BaseTool`
✅ `from app.settings import settings`
❌ `from .base import BaseTool`
❌ `from ..settings import settings`

### Code Style
- **No comments or docstrings** – self-documenting code only
- **PEP 8 style enforced**
- **Descriptive naming** instead of inline explanations

## 🛡️ Error Handling & Logging

- **structlog required** for all logs
- **Log all key steps** (tool calls, AI failures, storage ops)
- **Graceful fallback**: tools return `None` instead of raising exceptions
- **Agent provides user-friendly error messaging** in flow

## 🧪 Testing Standards

- **70% minimum coverage**
- **Fixtures** for metadata, mock images, and fake AI responses
- **Mock external APIs** (Gemini, GPT)
- **Separate test files** per module
- **Validate both happy paths and failure cases**

## 📋 Development Rules

- **Always update CLAUDE.md** after any structural or pattern changes
- **Keep code self-documenting** (no comments/docstrings)
- **Ensure type hints are used everywhere**
- **Use built-in `list` and `dict`** for type annotations
- **Use pipe operator (`|`) instead of `Optional`** for union types
- **Always use absolute imports** (never relative imports)
- **Each tool must support pluggable AI model selection**
- **Test with mocks** for all AI calls
- **Run linting, type check, and tests** locally before commits
- **Use conversational agent → tool orchestration**
- **Store artifacts in per-session directories**
- **All datetime operations use timezone-aware objects**

## 🔄 Critical Workflow

1. **Chat interface** presents friendly greeting
2. **Conversational agent** collects child details through natural dialogue
3. **Session manager** persists all chat history and collected data
4. **Agent extracts information** automatically from user responses
5. **When complete** → tools are orchestrated:
   - **Seed tool** creates character seeds
   - **Narrator tool** generates book content + scenes
   - **Illustrator tool** produces illustrations (using seeds + scenes)
   - **Storage tool** saves text + images to session directory
6. **Results displayed** in chat with session persistence