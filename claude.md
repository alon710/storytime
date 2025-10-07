# Storytime - Children's Book Character Generator

A conversational AI chatbot built with Streamlit and LangGraph that specializes in creating personalized therapeutic children's books with character illustrations using Google's Gemini image generation model.

## Overview

Storytime is a parental consultant chatbot that helps parents create custom therapeutic storybooks where their child becomes the hero who overcomes real-life challenges. The application guides parents through a 5-step workflow: challenge discovery, seed image generation, story narration, illustration, and PDF generation.

## Architecture

- **UI Framework**: Streamlit
- **AI Framework**: LangGraph (with LangChain integrations)
- **Conversational Model**: OpenAI (GPT-5)
- **Image Generation**: Google Gemini 2.0 Flash Preview
- **Chat History**: SQLite database (chat.db)
- **Checkpointing**: SQLite database (checkpoints.db) for debugging
- **Logging**: structlog

## Key Features

### 1. LangGraph Agent
- **StateGraph architecture** with explicit node-based workflow
- **Checkpointing** for time-travel debugging and state inspection
- **Human-in-the-loop approvals** using `interrupt()` for parent review
- Persistent conversation history using SQLite
- Session-based context management

### 2. Workflow Steps
1. **Challenge Discovery**: Gather information about child and challenge
2. **Seed Image Generation**: Create hero-style character reference from photo
3. **Story Narration**: Write therapeutic 8-page children's book
4. **Illustration**: Generate consistent illustrations (coming soon)
5. **PDF Generation**: Create printable book (coming soon)

### 3. Image Generation
- Creates children's book style character reference sheets
- Supports reference images for consistency
- Generates hero-style seed images for character consistency
- Saves images to temporary files
- Stores images in session artifacts

### 4. Session Management
- Thread-safe session context using threading.local
- Artifact storage (images, files, texts)
- Session-specific image galleries
- Temporary file management

### 5. File Upload Support
- Multi-file upload capability
- Automatic image reference management
- Temporary file cleanup

## Project Structure

```
storytime/
├── src/
│   ├── app.py                          # Main Streamlit application entry point
│   ├── ai/
│   │   ├── agent.py                    # ConversationalAgent with LangGraph
│   │   ├── graph_state.py              # AgentState TypedDict for LangGraph
│   │   ├── graph_nodes.py              # Graph nodes (agent, tools, approval)
│   │   ├── graph_builder.py            # StateGraph construction
│   │   ├── debug_utils.py              # Debugging utilities
│   │   └── tools/
│   │       ├── challenge_discovery.py  # Challenge data gathering tool
│   │       ├── seed_image_generator.py # Seed character image generation
│   │       └── narrator.py             # Book content generation
│   ├── core/
│   │   ├── settings.py                 # Pydantic settings configuration
│   │   ├── logger.py                   # structlog configuration
│   │   ├── session.py                  # Session context manager
│   │   ├── workflow_state.py           # Workflow state persistence
│   │   └── temp_files.py               # Temporary file management
│   ├── schemas/
│   │   ├── workflow.py                 # WorkflowState domain model
│   │   ├── challenge.py                # ChallengeData model
│   │   └── book.py                     # BookContent model
│   └── ui/
│       └── chat.py                     # Chat interface rendering
├── chat.db                             # SQLite chat history database
├── checkpoints.db                      # SQLite checkpoints for debugging
├── pyproject.toml                      # Project dependencies
└── .env.example                        # Environment variable template
```

## Setup

### 1. Environment Variables

Create a `.env` file in the `src/core/` directory:

```env
CONVERSATIONAL_AGENT_API_KEY=your_openai_api_key
CONVERSATIONAL_AGENT_MODEL_NAME=gpt-5
CONVERSATIONAL_AGENT_TEMPERATURE=0.7

SEED_IMAGE_GENERATOR_TOOL_API_KEY=your_google_api_key
SEED_IMAGE_GENERATOR_TOOL_MODEL_NAME=models/gemini-2.0-flash-preview-image-generation
SEED_IMAGE_GENERATOR_TOOL_TEMPERATURE=0.7
SEED_IMAGE_GENERATOR_TOOL_MAX_OUTPUT_TOKENS=8192

NARRATOR_TOOL_API_KEY=your_openai_api_key
NARRATOR_TOOL_MODEL_NAME=gpt-4o
NARRATOR_TOOL_TEMPERATURE=0.8
NARRATOR_TOOL_MAX_OUTPUT_TOKENS=4096

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

### LangGraph Agent ([src/ai/agent.py](src/ai/agent.py))

The agent uses **LangGraph's StateGraph** architecture:
- **Nodes**: agent (LLM), tools (execution), approval (human-in-the-loop)
- **State**: AgentState with messages, workflow_state, artifacts
- **Checkpointing**: SqliteSaver for debugging and time-travel
- **Memory**: SQLChatMessageHistory for conversation display

Key methods:
- `chat(message, files, session_id)`: Main interaction method

### Graph Structure ([src/ai/graph_builder.py](src/ai/graph_builder.py))

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌─────────┐    tool calls    ┌───────┐
│  agent  ├─────────────────►│ tools │
└────┬────┘                   └───┬───┘
     │                            │
     │ needs approval             │ loop back
     ▼                            ▼
┌──────────┐                 ┌─────────┐
│ approval │◄────────────────┤  agent  │
└────┬─────┘                 └─────────┘
     │
     │ approved
     ▼
┌─────────┐
│   END   │
└─────────┘
```

### Graph Nodes ([src/ai/graph_nodes.py](src/ai/graph_nodes.py))

1. **agent_node**: Calls LLM with tools bound, decides next action
2. **tool_node**: Executes tool calls (discover_challenge, generate_seed_image, generate_book_content)
3. **approval_node**: Human-in-the-loop using `interrupt()` for parent approval
4. **route_decision**: Conditional routing (tools | approval | end)

### State Management

**AgentState** (LangGraph execution state):
- `messages`: Conversation history
- `session_id`: Session identifier
- `workflow_state`: Business domain state (nested)
- `artifacts`: Session artifacts

**WorkflowState** (Business domain state):
- `current_step`: Current workflow step
- `challenge_data`: Challenge information
- `seed_image_path`: Generated seed image path
- `book_content`: Generated book content
- `approvals`: Step approval tracking

### Tools ([src/ai/tools/](src/ai/tools/))

1. **discover_challenge**: Gathers and validates child challenge information
2. **generate_seed_image**: Creates hero-style character reference from photo
3. **generate_book_content**: Writes therapeutic children's book

### Session Context ([src/core/session.py](src/core/session.py))

Thread-safe session management:
- **Artifact types**: images, files, texts, available_images
- **Thread-local** current session tracking
- **Lock-based** concurrent access protection
- **Session-specific** artifact storage

### Workflow State Management ([src/core/workflow_state.py](src/core/workflow_state.py))

Persists business workflow state:
- SQLite storage for WorkflowState
- Thread-safe operations
- Step completion tracking
- Approval management

### Settings Configuration ([src/core/settings.py](src/core/settings.py))

Hierarchical Pydantic settings:
- **ConversationalAgentSettings**: LLM configuration and system prompt
- **SeedImageGeneratorToolSettings**: Image generation model
- **NarratorToolSettings**: Book generation model
- **AppSettings**: UI configuration
- **ChatSettings**: Chat interface settings

All settings support environment variable overrides.

## Debugging

### Checkpoint Inspection

```python
from ai.debug_utils import print_checkpoint_history, get_workflow_state_history

# View checkpoint history
print_checkpoint_history("session_id")

# View workflow state evolution
workflow_history = get_workflow_state_history("session_id")
```

### Graph Visualization

When `IS_DEVELOPMENT_MODE=true`, the app generates `graph_visualization.mmd`:

```python
from ai.debug_utils import visualize_graph_from_file

# Display graph
visualize_graph_from_file()
# Paste output into https://mermaid.live
```

### Time-Travel Debugging

```python
# Access checkpoint state
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
config = {"configurable": {"thread_id": "session_id"}}

# List all checkpoints
for checkpoint_tuple in checkpointer.list(config):
    print(checkpoint_tuple.checkpoint)
```

## Usage

1. Start the application
2. Tell the agent about your child and their challenge
3. Upload a photo of your child
4. Review and approve the generated seed image
5. Review and approve the generated story
6. (Coming soon) Review illustrations and generate PDF

## Chat Flow

1. User uploads image(s) → Saved to temp files → Added to session artifacts
2. User sends message → Enhanced with workflow context
3. LangGraph executes:
   - agent_node → Decides to call tool or finish
   - tool_node → Executes tools (discover_challenge, generate_seed_image, etc.)
   - approval_node → Pauses for parent approval using `interrupt()`
4. Tool generates images → Saved to temp files → Added to session artifacts
5. Response returned with text + generated images → Displayed in UI
6. Checkpoint saved → Enables debugging and state inspection

## Dependencies

- `streamlit>=1.50.0` - Web UI framework
- `langchain>=0.3.0` - AI framework integrations
- `langchain-openai>=0.2.0` - OpenAI integration
- `langchain-google-genai>=2.0.0` - Google Gemini integration
- `langchain-community>=0.3.0` - Community tools
- `langgraph>=0.6.8` - LangGraph agent framework
- `langgraph-checkpoint-sqlite>=1.0.0` - SQLite checkpointing
- `pydantic>=2.11.9` - Settings validation
- `structlog>=24.0.0` - Structured logging
- `python-dotenv>=1.0.0` - Environment variable loading

## Development

The project uses:
- **Python 3.10+**
- **Ruff** for linting (line length: 120)
- **uv** for dependency management
- **SQLite** for chat history and checkpoints

Enable development mode in `.env`:
```env
IS_DEVELOPMENT_MODE=true
```

This enables:
- Verbose graph execution logging
- Automatic graph visualization export
- Enhanced debugging output

## Why LangGraph?

LangGraph provides significant advantages over LangChain's AgentExecutor:

1. **Debugging**: Checkpoint-based time-travel debugging
2. **Visibility**: Explicit node-based architecture vs black-box executor
3. **Control**: Fine-grained control over agent flow and routing
4. **Human-in-the-loop**: Natural integration with `interrupt()` for approvals
5. **Observability**: Inspect state at every step of execution
6. **Reliability**: Reproducible execution with checkpoint replay
