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
app.py              # Streamlit chat UI with file upload support
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
- **SQLAlchemy (async)** - Database ORM with async support
- **aiosqlite** - Async SQLite driver
- **Pydantic** - Data validation & config
- **Pillow** - Image processing and reference photo handling
- **structlog** - Structured logging
- **Streamlit** - Chat-based web UI with file upload support

### Development
- **uv** - Package management
- **pyproject.toml** - Project config
- **pytest** (+ coverage, asyncio, mocking) - Testing framework
- **Ruff** - Linting & formatting
- **ty** - Type checker

## 🤖 Agent & Tool Design

### Main Conversational Agent (`agent.py`)
- **LangChain-based conversational flow** with natural language processing
- **Session-aware context** - remembers previous conversations via SQLite
- **Smart information extraction** - automatically parses user responses
- **Image handling** - processes uploaded reference photos
- **Ensures all required details are collected:**
  - Child's name, age, gender
  - Challenge/theme
  - Reference images (uploaded via chat interface)
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

## 🗄️ Database Layer

### SQLAlchemy Models (`app/database/models.py`)
- **Session**: Core session tracking with UUID
- **SessionData**: Child information and completion status
- **ChatHistory**: Message history with timezone-aware timestamps
- **GeneratedContent**: Story artifacts and file paths

### Session Manager (`app/database/session_manager.py`)
- **Async database operations** using SQLAlchemy async
- **Image serialization** using pickle/base64 for reference photos
- **Session lifecycle management** with proper cleanup
- **Chat history persistence** with chronological ordering
- **Missing field tracking** for conversation flow
- **Reference image storage/retrieval** for seed generation

### Database Features
- **Timezone-aware timestamps** using UTC (`datetime.now(timezone.utc)`)
- **JSON field support** for flexible data storage
- **Async session management** for non-blocking operations
- **Auto-initialization** of tables on first run

## 💬 Chat UI Implementation

### Streamlit Chat Components (`app.py`)
- **st.chat_input** with `accept_file="multiple"` support
- **ChatInputValue handling** - properly extracts text and files
- **st.chat_message** for conversation display
- **PIL Image processing** for uploaded reference photos
- **Session state management** for UI persistence
- **Real-time chat history** with assistant responses

### File Upload Features
- **Multi-file image upload** via chat interface
- **Image preview** with thumbnails in chat
- **PIL Image conversion** and storage in session state
- **Reference image passing** to seed generation tool
- **Error handling** for unsupported file types

### Chat Flow Implementation
1. User sends message with optional image uploads via `st.chat_input`
2. System extracts text using `user_input.text` and files using `user_input.files`
3. Images converted to PIL format and stored in session
4. Agent receives message and reference images via `chat()` method
5. Natural language processing extracts child information
6. Database persists chat messages and session data
7. Tools are invoked when all required information is collected

## 🚀 Getting Started for Developers

### Prerequisites
- **Python 3.12+** installed
- **uv** package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **API keys** for OpenAI and Google GenAI

### Quick Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repository>
   cd storytime
   uv sync  # Install all dependencies
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # OPENAI_API_KEY=your_openai_key_here
   # GOOGLE_API_KEY=your_google_genai_key_here
   ```

3. **Run the application:**
   ```bash
   uv run streamlit run app.py
   ```
   - Visit `http://localhost:8501` in your browser
   - Start chatting to create personalized stories!

### Understanding the Codebase

#### 🎯 Entry Points (Start Here)
- **`app.py`**: Streamlit chat UI - see how user interaction works
- **`app/agent.py`**: Main conversational agent - understand LangChain integration
- **`app/settings.py`**: Configuration hub - see how models are selected

#### 🔧 Key Components Deep Dive
- **Database layer**: `app/database/` - SQLAlchemy models and async operations
- **Tools directory**: `app/tools/` - AI-powered tools for story generation
- **LangChain integration**: Agent orchestration with natural language processing
- **Multi-model support**: Different AI models for different tasks

#### 📁 File Purpose Guide
- **`base.py`**: LangChain-compatible base class for all tools
- **`seed.py`**: Character image generation with reference photo support
- **`narrator.py`**: Story content and scene description generation
- **`illustrator.py`**: Page illustration creation with consistency
- **`storage.py`**: File system persistence for generated content
- **`session_manager.py`**: Database operations and session management
- **`models.py`**: SQLAlchemy data models

### 🔨 Common Development Tasks

#### Adding a New Tool
1. Create new file in `app/tools/`
2. Inherit from `BaseTool` in `app/tools/base.py`
3. Implement required methods:
   ```python
   async def execute(self, ...): # Main business logic
   async def _arun(self, **kwargs): # LangChain compatibility
   ```
4. Add tool to agent in `app/agent.py` constructor
5. Update model configuration in `app/settings.py` if needed

#### Modifying the Conversation Flow
1. Update system prompt in `app/agent.py` (`_get_system_prompt()`)
2. Modify information extraction in `_extract_and_update_session_data()`
3. Update database models if new fields are needed
4. Test conversation flow with various inputs

#### Adding New Database Fields
1. Update SQLAlchemy models in `app/database/models.py`
2. Add getter/setter methods in `app/database/session_manager.py`
3. Update agent's information extraction logic
4. Add validation and type hints

### 🧪 Testing and Quality Assurance

#### Running Tests
```bash
uv run pytest                    # Run all tests
uv run pytest --cov             # Run with coverage report
uv run pytest -v                # Verbose output
uv run pytest tests/test_agent.py # Run specific test file
```

#### Code Quality Checks
```bash
uv run ruff check               # Linting
uv run ruff format              # Auto-formatting
uv run mypy app/                # Type checking
```

#### Pre-commit Checklist
- [ ] Tests pass (`uv run pytest`)
- [ ] No linting errors (`uv run ruff check`)
- [ ] Type checking passes (`uv run mypy app/`)
- [ ] Manual testing with Streamlit UI
- [ ] Update CLAUDE.md if structure changed

### 🐛 Troubleshooting Guide

#### Common Issues and Solutions

1. **ChatInputValue Error**
   - **Problem**: `type 'ChatInputValue' is not supported`
   - **Solution**: Streamlit returns special objects for file uploads, extract using `.text` and `.files`
   - **Fix**: Update chat input handling in `app.py`

2. **Pydantic Field Override Error**
   - **Problem**: `Field defined on a base class was overridden`
   - **Solution**: Add explicit type annotations to all class attributes
   - **Example**: `name: str = "tool_name"` instead of `name = "tool_name"`

3. **OpenAI API Key Error**
   - **Problem**: `The api_key client option must be set`
   - **Solution**: Pass `api_key` parameter to `ChatOpenAI()` constructor
   - **Check**: Verify `.env` file exists and contains `OPENAI_API_KEY`

4. **Google GenAI Authentication**
   - **Problem**: API key not being passed to Gemini models
   - **Solution**: Pass `api_key` to `genai.Client()` constructor
   - **Check**: Verify `GOOGLE_API_KEY` in environment

5. **Database Connection Issues**
   - **Problem**: SQLite file permissions or async handling
   - **Solution**: Check file permissions, ensure async context managers are used
   - **Debug**: Enable SQLAlchemy echo: `create_async_engine(database_url, echo=True)`

6. **LangChain Tool Invocation Error**
   - **Problem**: Unexpected arguments in tool `_arun()` method
   - **Solution**: Accept `**kwargs` and handle different argument formats
   - **Pattern**: Check for `args` list or direct kwargs in tool methods

#### Debug Tips
- **Enable verbose logging**: Set `AgentExecutor(verbose=True)` in agent
- **SQLAlchemy debugging**: Use `echo=True` in engine creation
- **Structured logging**: Check logs for tool execution details
- **Streamlit debugging**: Use `st.write()` to inspect variables
- **Database inspection**: Use SQLite browser to check data

#### Getting Help
- Check existing tests for examples
- Review LangChain documentation for agent patterns
- Examine structured logs for execution flow
- Test individual components in isolation

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
- **All datetime operations use timezone-aware objects** (`datetime.now(timezone.utc)`)
- **Handle ChatInputValue objects** properly in Streamlit UI

## 🔄 Critical Workflow

1. **Chat interface** presents friendly greeting via Streamlit
2. **User interaction** through chat with optional image uploads
3. **Conversational agent** collects child details through natural dialogue
4. **Session manager** persists all chat history and collected data in SQLite
5. **Agent extracts information** automatically from user responses using regex/NLP
6. **Reference images** processed and stored for personalization
7. **When complete** → tools are orchestrated via LangChain:
   - **Seed tool** creates character seeds using reference images
   - **Narrator tool** generates book content + scene descriptions
   - **Illustrator tool** produces illustrations (using seeds + scenes + continuity)
   - **Storage tool** saves text + images to session directory
8. **Results displayed** in chat with full session persistence and image previews