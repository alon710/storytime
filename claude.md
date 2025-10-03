# Storytime - Children's Book Character Generator

A conversational AI chatbot built with Streamlit and LangChain that specializes in generating children's book style character illustrations using Google's Gemini image generation model.

## Overview

Storytime is a parental consultant chatbot that creates magical children's book illustrations from uploaded photos. The application generates character reference sheets showing children in two poses (front and side view) using various artistic styles like watercolor, retro mid-century, modern digital, 3D animation, and paper cut-out styles.

## Architecture

- **UI Framework**: Streamlit
- **AI Framework**: LangChain
- **Conversational Model**: OpenAI (GPT-5)
- **Image Generation**: Google Gemini 2.0 Flash Preview
- **Chat History**: SQLite database
- **Logging**: structlog

## Key Features

### 1. Conversational Agent
- Powered by OpenAI's language model
- Tool-calling capabilities for image generation
- Persistent conversation history using SQLite
- Session-based context management

### 2. Image Generation Tool
- Creates children's book style character reference sheets
- Supports reference images for consistency
- Multiple artistic styles (watercolor, retro, modern digital, 3D animation, paper cut-out)
- Generates dual-pose images (front and side view)
- 800x800 square format output

### 3. Session Management
- Thread-safe session context using threading.local
- Artifact storage (images, files, texts)
- Session-specific image galleries
- Temporary file management

### 4. File Upload Support
- Multi-file upload capability
- Automatic image reference management
- Temporary file cleanup

## Project Structure

```
storytime/
├── src/
│   ├── app.py                      # Main Streamlit application entry point
│   ├── ai/
│   │   ├── agent.py                # ConversationalAgent with LangChain
│   │   └── tools/
│   │       └── images.py           # Image generation tool using Gemini
│   ├── core/
│   │   ├── settings.py             # Pydantic settings configuration
│   │   ├── logger.py               # structlog configuration
│   │   ├── session.py              # Session context manager
│   │   └── temp_files.py           # Temporary file management
│   └── ui/
│       └── chat.py                 # Chat interface rendering
├── chat.db                         # SQLite chat history database
├── pyproject.toml                  # Project dependencies
└── .env.example                    # Environment variable template
```

## Setup

### 1. Environment Variables

Create a `.env` file in the `src/core/` directory:

```env
CONVERSATIONAL_AGENT_API_KEY=your_openai_api_key
CONVERSATIONAL_AGENT_MODEL_NAME=gpt-5
CONVERSATIONAL_AGENT_TEMPERATURE=0.7

IMAGES_GENERATOR_TOOL_API_KEY=your_google_api_key
IMAGES_GENERATOR_TOOL_MODEL_NAME=models/gemini-2.0-flash-preview-image-generation
IMAGES_GENERATOR_TOOL_TEMPERATURE=0.7
IMAGES_GENERATOR_TOOL_MAX_OUTPUT_TOKENS=8192

IS_DEVELOPMENT_MODE=false
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 3. Run the Application

```bash
streamlit run src/app.py
```

## Technical Details

### ConversationalAgent ([src/ai/agent.py](src/ai/agent.py))

The agent uses:
- **LangChain's `create_tool_calling_agent`** with OpenAI
- **Tool**: `generate_image` for creating illustrations
- **Memory**: `RunnableWithMessageHistory` with SQLite backend
- **Prompt Template**: System prompt + chat history + user input + agent scratchpad

Key methods:
- `chat(message, files, session_id)`: Main interaction method that processes messages and files

### Image Generation Tool ([src/ai/tools/images.py](src/ai/tools/images.py))

The `generate_image` tool:
- Uses Google's Gemini 2.0 Flash Preview model
- Accepts text prompts and optional reference images
- Returns list of generated image paths
- Saves images to temporary files
- Stores images in session artifacts

### Session Context ([src/core/session.py](src/core/session.py))

Thread-safe session management:
- **Artifact types**: images, files, texts, available_images
- **Thread-local** current session tracking
- **Lock-based** concurrent access protection
- **Session-specific** artifact storage

### Settings Configuration ([src/core/settings.py](src/core/settings.py))

Hierarchical Pydantic settings:
- **ConversationalAgentSettings**: LLM configuration and system prompt
- **ImagesGeneratorToolSettings**: Image generation model and prompts
- **AppSettings**: UI configuration (title, icon)
- **ChatSettings**: Chat interface settings

All settings support environment variable overrides.

### Temporary File Management ([src/core/temp_files.py](src/core/temp_files.py))

Handles temporary file storage:
- `save_from_base64()`: Saves base64 encoded images
- `save_file()`: Saves uploaded file bytes
- `cleanup_all_files()`: Cleanup utility
- Tracks all created files for lifecycle management

## Usage

1. Start the application
2. Upload a photo of a child (optional)
3. Chat with the parental consultant
4. The agent will automatically generate character reference sheets in children's book style
5. Images persist in the session and can be used as references for subsequent generations

## Chat Flow

1. User uploads image(s) → Saved to temp files → Added to session artifacts
2. User sends message → Enhanced with available images context
3. Agent processes with LangChain → May call `generate_image` tool
4. Tool generates images → Saved to temp files → Added to session artifacts
5. Response returned with text + generated images → Displayed in UI

## Dependencies

- `streamlit>=1.50.0` - Web UI framework
- `langchain>=0.3.0` - AI agent framework
- `langchain-openai>=0.2.0` - OpenAI integration
- `langchain-google-genai>=2.0.0` - Google Gemini integration
- `langchain-community>=0.3.0` - Community tools
- `pydantic>=2.11.9` - Settings validation
- `structlog>=24.0.0` - Structured logging
- `python-dotenv>=1.0.0` - Environment variable loading

## Development

The project uses:
- **Python 3.10+**
- **Ruff** for linting (line length: 120)
- **uv** for dependency management
- **SQLite** for chat history persistence

Enable development mode in `.env`:
```env
IS_DEVELOPMENT_MODE=true
```

This enables verbose agent execution logging.
