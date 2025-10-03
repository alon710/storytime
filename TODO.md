# Storytime - Personalized Children's Book Generator - TODO

This document tracks all tasks needed to transform the current application into a complete personalized children's book creation platform. The app helps parents generate a personalized children's book where their child is the hero facing a specific challenge.

---

## 1. Infrastructure & Setup

### ~~1.1 Basic Settings Configuration~~
**Status**: DONE
~~Implemented Pydantic-based settings with environment variable support for agents and tools.~~

### ~~1.2 Logging System~~
**Status**: DONE
~~Implemented structlog-based logging with colored console output and ISO timestamps.~~

### ~~1.3 Basic Session Context~~
**Status**: DONE
~~Implemented thread-safe session context for storing artifacts (images, files, texts) per session.~~

### ~~1.4 Temporary File Management~~
**Status**: DONE
~~Implemented temp file manager for saving base64 and binary file content with cleanup capabilities.~~

### 1.5 Workflow State Management
**Status**: TODO
**Description**: Extend session context to track the book creation workflow state per session, including which tools have been completed, what data each tool produced, and what has been approved by the parent.
**Files**: `src/core/workflow_state.py`, `src/core/session.py`
**Acceptance Criteria**:
- Define `WorkflowStep` type alias:
  - `WorkflowStep = Literal["discovery", "seed_image", "narration", "illustration", "pdf_generation", "completed"]`
- Create `WorkflowState` BaseModel with fields:
  - `current_step: WorkflowStep`
  - `challenge_data: Optional[ChallengeData]`
  - `seed_image_path: Optional[Path]` (from pathlib)
  - `book_content: Optional[BookContent]`
  - `illustrations: Optional[dict[int, Path]]` (page number -> image path)
  - `pdf_path: Optional[Path]` (from pathlib)
  - `approvals: dict[WorkflowStep, bool]` (step -> approved status)
  - `created_at: datetime`
  - `updated_at: datetime`
- Implement `WorkflowStateManager` class with methods:
  - `get_workflow_state(session_id: str) -> WorkflowState`
  - `update_workflow_state(session_id: str, **updates) -> None`
  - `is_step_completed(session_id: str, step: WorkflowStep) -> bool`
  - `mark_step_approved(session_id: str, step: WorkflowStep) -> None`
  - `can_proceed_to_next_step(session_id: str) -> bool`
- Persist workflow state to SQLite database
- Thread-safe with locking mechanism
**Dependencies**: 1.1, 1.2, 1.3
**Notes**: This is critical for the agent to know where in the workflow each session is and make appropriate decisions.

### 1.6 Data Models Library
**Status**: TODO
**Description**: Create a centralized module for all Pydantic BaseModels used across tools and agent responses.
**Files**: `src/models/__init__.py`, `src/models/challenge.py`, `src/models/book.py`, `src/models/tool_responses.py`
**Acceptance Criteria**:
- Define `ChallengeData` BaseModel:
  - `challenge_type: str` (e.g., "fear of dark", "starting school", "new sibling")
  - `details: str` (parent's detailed description)
  - `child_name: str`
  - `child_age: int`
  - `child_gender: Optional[str]`
  - `desired_outcome: str` (what the parent hopes the child will learn/feel)
  - `additional_context: Optional[str]`
- Define `BookPage` BaseModel:
  - `page_number: int`
  - `title: str`
  - `story_content: str`
  - `scene_description: str` (for illustrator)
  - `illustration_path: Optional[Path]` (from pathlib)
- Define `BookContent` BaseModel:
  - `book_title: str`
  - `pages: list[BookPage]`
  - `total_pages: int`
  - `style_guidance: str` (overall artistic style)
- Define `ToolResponse[T]` generic BaseModel:
  - `success: bool`
  - `data: Optional[T]`
  - `error_message: Optional[str]`
  - `metadata: dict[str, Any]`
- All models must use strict typing and validation
**Dependencies**: 1.1
**Notes**: Centralizing models ensures type safety and consistency across all tools.

---

## 2. Tools Implementation

### ~~2.1 Basic Image Generation (Generic)~~
**Status**: DONE
~~Implemented generic image generation tool using Google Gemini with reference image support.~~

### 2.2 Challenge Discovery Tool
**Status**: TODO
**Description**: Implement a tool that conducts a conversational discovery process to understand the child's challenge in detail. This tool should extract and structure information from parent's input.
**Files**: `src/ai/tools/challenge_discovery.py`, `src/core/settings.py`
**Acceptance Criteria**:
- Create `discover_challenge` LangChain tool function
- Input parameters:
  - `child_name: str`
  - `child_age: int`
  - `challenge_description: str`
  - `desired_outcome: str`
  - `additional_context: Optional[str] = None`
- Returns `ToolResponse[ChallengeData]`
- Validates all required fields are present
- Stores result in workflow state
- Add `ChallengeDiscoveryToolSettings` to settings.py with configurable prompts
- Tool should guide the agent to ask follow-up questions if information is incomplete
**Dependencies**: 1.6
**Notes**: This is the first step in the book creation process. The tool itself doesn't need to be conversational - the main agent handles the conversation and calls this tool once it has gathered sufficient information.

### 2.3 Seed Image Generator Tool
**Status**: TODO
**Description**: Generate a seed character image from the child's photo that will be used as reference for all subsequent illustrations in the book.
**Files**: `src/ai/tools/seed_image.py`, `src/core/settings.py`
**Acceptance Criteria**:
- Create `generate_seed_image` LangChain tool function
- Input parameters:
  - `child_image_path: Path` (uploaded photo, from pathlib)
  - `challenge_data: ChallengeData` (for context)
  - `parent_description: Optional[str] = None` (additional styling requests)
- Returns `ToolResponse[Path]` (path to generated seed image)
- Uses Google Gemini image generation model
- System prompt should create a hero-style character suitable for children's book
- Stores result path in workflow state as `seed_image_path`
- Add `SeedImageGeneratorToolSettings` to settings.py
- Save generated image with prefix `seed_image_`
**Dependencies**: 1.6, 2.2
**Notes**: This is distinct from the generic image generator. The seed image is specifically designed to be a character reference for the entire book. Consider creating character in neutral pose, front-facing, suitable as reference.

### 2.4 Narrator Tool
**Status**: TODO
**Description**: Generate the complete book content (title and all pages) based on the child's challenge. Each page includes title, story content, and scene description for illustration.
**Files**: `src/ai/tools/narrator.py`, `src/core/settings.py`
**Acceptance Criteria**:
- Create `generate_book_content` LangChain tool function
- Input parameters:
  - `challenge_data: ChallengeData`
  - `num_pages: int = 8` (configurable, default 8 pages)
  - `style_preference: Optional[str] = None` (e.g., "rhyming", "adventure", "gentle")
- Returns `ToolResponse[BookContent]`
- Uses OpenAI or Claude for text generation with specialized system prompt
- Each page must include:
  - Page number (1-indexed)
  - Page title
  - Age-appropriate story content (2-4 sentences per page)
  - Detailed scene description for illustrator (3-5 sentences describing visual elements, mood, composition)
- Book should follow narrative arc: introduction → challenge appears → hero struggles → hero overcomes → resolution/lesson
- Validates that child's name appears in story and child is the hero
- Stores result in workflow state as `book_content`
- Add `NarratorToolSettings` to settings.py with system prompt configuration
**Dependencies**: 1.6, 2.2
**Notes**: This is a critical creative tool. The system prompt should be carefully crafted to create age-appropriate, engaging, and therapeutic content. Consider using a higher-quality LLM model for this task.

### 2.5 Illustrator Tool
**Status**: TODO
**Description**: Generate an illustration for a specific book page using the seed image and scene description. Supports using up to 3 previous page illustrations for visual continuity.
**Files**: `src/ai/tools/illustrator.py`, `src/core/settings.py`
**Acceptance Criteria**:
- Create `generate_page_illustration` LangChain tool function
- Input parameters:
  - `seed_image_path: Path` (character reference, from pathlib)
  - `scene_description: str` (from narrator)
  - `page_number: int`
  - `previous_illustrations: list[Path] = []` (max 3 previous page image paths, from pathlib)
  - `style_guidance: str` (from BookContent)
- Returns `ToolResponse[Path]` (path to generated illustration)
- Uses Google Gemini image generation model
- System prompt should emphasize:
  - Character consistency (using seed image)
  - Visual continuity (using previous illustrations)
  - Scene accuracy (following scene description)
  - Children's book illustration style
  - Age-appropriate content
- Generated images should be 1024x1024 or suitable for PDF printing
- Save with prefix `page_{page_number}_illustration_`
- Store result in workflow state `illustrations` dict
- Add `IllustratorToolSettings` to settings.py
**Dependencies**: 1.6, 2.3, 2.4
**Notes**: This tool will be called multiple times (once per page). The agent should call it sequentially for pages 1, 2, 3, etc., passing previous illustrations for continuity.

### 2.6 PDF Generator Tool
**Status**: TODO
**Description**: Generate the final PDF book from all pages (text + illustrations).
**Files**: `src/ai/tools/pdf_generator.py`, `src/core/settings.py`, `pyproject.toml` (add dependencies)
**Acceptance Criteria**:
- Create `generate_pdf_book` LangChain tool function
- Input parameters:
  - `book_content: BookContent`
  - `illustrations: dict[int, Path]` (page number -> image path, from pathlib)
  - `output_filename: Optional[str] = None` (auto-generate if not provided)
- Returns `ToolResponse[Path]` (path to generated PDF)
- Uses `reportlab` or `weasyprint` library for PDF generation
- PDF layout:
  - Cover page with book title
  - Each page: illustration at top (60% of page), text at bottom (40% of page)
  - Page numbers
  - Clean, child-friendly typography
  - A4 or Letter size
- Save PDF with prefix `book_`
- Store result path in workflow state as `pdf_path`
- Add `PDFGeneratorToolSettings` to settings.py
- Add `reportlab>=4.0.0` or `weasyprint>=60.0` to pyproject.toml dependencies
**Dependencies**: 1.6, 2.4, 2.5
**Notes**: This is the final output. Consider adding options for different layouts or page sizes in future iterations.

---

## 3. Agent Orchestration & Logic

### ~~3.1 Basic Conversational Agent~~
**Status**: DONE
~~Implemented LangChain-based conversational agent with tool calling and chat history.~~

### 3.2 Workflow-Aware Agent System Prompt
**Status**: TODO
**Description**: Update the agent's system prompt to understand the book creation workflow and guide parents through each step.
**Files**: `src/core/settings.py`, `src/ai/agent.py`
**Acceptance Criteria**:
- Create comprehensive system prompt that explains:
  - The agent's role as a children's book creation assistant
  - The 5-step workflow: Challenge Discovery → Seed Image → Narration → Illustration → PDF Generation
  - How to determine which step the session is currently on
  - When to call each tool
  - How to ask for parent approval at each major step
  - When to end the conversation (after PDF approval)
- Agent should be warm, supportive, and professional
- Agent should explain each step before executing it
- Agent should never skip steps or rush the process
- System prompt should be configurable via settings
**Dependencies**: 1.5, 3.1
**Notes**: The system prompt is critical for proper agent behavior. It should be detailed and include examples of good conversation flow.

### 3.3 Workflow State Integration in Agent
**Status**: TODO
**Description**: Modify the ConversationalAgent to be aware of and use the workflow state for each session.
**Files**: `src/ai/agent.py`
**Acceptance Criteria**:
- In `chat()` method, load current workflow state before processing message
- Pass workflow state context to the agent in the prompt (e.g., "Current step: discovery, Completed steps: none")
- After each tool call, update workflow state appropriately
- Implement logic to prevent out-of-order tool execution (e.g., can't generate illustrations before narration)
- Add workflow state summary to enhanced message context
- Log workflow state transitions
**Dependencies**: 1.5, 3.1, 3.2
**Notes**: The agent must be stateful and aware of the workflow progression.

### 3.4 Tool Registration and Orchestration
**Status**: TODO
**Description**: Register all tools with the agent and implement proper tool orchestration logic.
**Files**: `src/ai/agent.py`, `src/ai/tools/__init__.py`
**Acceptance Criteria**:
- Update `self.tools` list in ConversationalAgent to include:
  - `discover_challenge` (2.2)
  - `generate_seed_image` (2.3)
  - `generate_book_content` (2.4)
  - `generate_page_illustration` (2.5)
  - `generate_pdf_book` (2.6)
- Create `src/ai/tools/__init__.py` to export all tools
- Ensure tool descriptions are clear and guide the agent on when to use each tool
- Tools should have proper error handling and return ToolResponse objects
**Dependencies**: 2.2, 2.3, 2.4, 2.5, 2.6, 3.1
**Notes**: The agent should have access to all tools but use them in the correct sequence based on workflow state.

### 3.5 Approval Mechanism
**Status**: TODO
**Description**: Implement logic for the agent to ask for and track parent approvals at key workflow steps.
**Files**: `src/ai/agent.py`, `src/core/workflow_state.py`
**Acceptance Criteria**:
- After completing each major step (discovery, seed image, book content, all illustrations, PDF), agent should:
  - Present the result to the parent
  - Ask for explicit approval
  - Wait for parent response before proceeding
- Implement approval detection logic (e.g., keywords like "yes", "looks good", "approve", "continue")
- Store approvals in workflow state `approvals` dict
- Agent should allow parent to request changes/regeneration
- If parent requests changes, agent should redo the step with updated parameters
**Dependencies**: 1.5, 3.3
**Notes**: This ensures parent control over the process. Consider implementing both explicit approval commands and natural language approval detection.

### 3.6 Conversation Termination Logic
**Status**: TODO
**Description**: Implement logic to gracefully end the conversation after PDF is approved.
**Files**: `src/ai/agent.py`
**Acceptance Criteria**:
- After PDF is generated and approved, agent should:
  - Provide final message with PDF download information
  - Thank the parent
  - Mark workflow state as `completed`
  - Indicate that the session is complete
- Agent should not accept new book creation requests in the same session after completion
- Agent should suggest starting a new session if parent wants to create another book
- Update system prompt to include end-of-conversation behavior
**Dependencies**: 2.6, 3.2, 3.5
**Notes**: The conversation should have a clear ending. Consider adding a final summary of what was created.

### 3.7 Error Handling and Recovery
**Status**: TODO
**Description**: Implement comprehensive error handling and recovery mechanisms for tool failures.
**Files**: `src/ai/agent.py`, `src/ai/tools/*.py`
**Acceptance Criteria**:
- All tools should return `ToolResponse` with success/error indication
- Agent should detect tool failures and inform parent
- Agent should offer to retry failed operations
- Implement retry logic with exponential backoff for API failures
- Log all errors with context (session_id, workflow step, tool name)
- Agent should not proceed if a critical step fails
- Parent should have option to skip/retry/modify parameters on failure
**Dependencies**: 1.6, 3.4
**Notes**: Robust error handling is critical for good user experience. Consider different recovery strategies for different types of errors (API failures vs. validation errors vs. content issues).

---

## 4. Chat Interface & UI

### ~~4.1 Basic Streamlit Chat Interface~~
**Status**: DONE
~~Implemented basic chat interface with message history and file upload support.~~

### 4.2 Workflow Progress Indicator
**Status**: TODO
**Description**: Add a visual progress indicator in the Streamlit UI showing the current workflow step and completed steps.
**Files**: `src/ui/chat.py`, `src/ui/components.py`
**Acceptance Criteria**:
- Create a progress bar or stepper component showing 5 steps:
  1. Challenge Discovery
  2. Seed Image Generation
  3. Story Creation
  4. Illustration Generation
  5. PDF Generation
- Highlight current step
- Show checkmarks for completed steps
- Show approval status for each step
- Update in real-time as workflow progresses
- Display in sidebar or at top of chat interface
**Dependencies**: 1.5, 4.1
**Notes**: This helps parents understand where they are in the process. Use Streamlit's sidebar or custom components.

### 4.3 Book Preview Component
**Status**: TODO
**Description**: Create a UI component to preview the book content (pages + illustrations) before PDF generation.
**Files**: `src/ui/components.py`, `src/ui/chat.py`
**Acceptance Criteria**:
- Create `render_book_preview()` function
- Display book title
- Show each page with:
  - Page number
  - Page title (if present)
  - Story text
  - Illustration (if generated)
- Use tabs or accordion for multiple pages
- Add "Approve" and "Request Changes" buttons
- Preview should be scrollable and well-formatted
**Dependencies**: 2.4, 2.5, 4.1
**Notes**: This gives parents a clear view of the book before final PDF generation. Consider making it interactive.

### 4.4 PDF Download Component
**Status**: TODO
**Description**: Add a download button for the final PDF in the Streamlit UI.
**Files**: `src/ui/chat.py`
**Acceptance Criteria**:
- After PDF is generated, display a download button
- Use `st.download_button()` with PDF file
- Button should be prominently displayed
- Include PDF metadata (filename, size, creation date)
- Add option to generate PDF again with different settings
**Dependencies**: 2.6, 4.1
**Notes**: Make sure the download button persists in the UI even if user scrolls up in conversation history.

### 4.5 Session Management UI
**Status**: TODO
**Description**: Add UI controls for session management (reset, start new book, view history).
**Files**: `src/ui/chat.py`
**Acceptance Criteria**:
- Add "Start New Book" button that clears current session and creates new one
- Add "Reset Current Book" button that clears workflow but keeps conversation history
- Display current session ID
- Add option to view/load previous sessions (if multiple books created)
- Confirmation dialog before resetting or starting new session
**Dependencies**: 1.5, 4.1
**Notes**: This prevents accidental data loss and allows parents to create multiple books.

### 4.6 Enhanced File Upload with Preview
**Status**: TODO
**Description**: Improve file upload experience with image preview and validation.
**Files**: `src/ui/chat.py`
**Acceptance Criteria**:
- Show thumbnail preview of uploaded child photo
- Validate file type (only images allowed)
- Validate file size (max 10MB)
- Show upload status and filename
- Allow removing uploaded file before submission
- Display helpful hints (e.g., "Upload a clear photo of your child's face")
**Dependencies**: 4.1
**Notes**: Better upload UX reduces errors and improves user confidence.

---

## 5. QA, Testing & Deployment

### 5.1 Unit Tests for Tools
**Status**: TODO
**Description**: Create unit tests for all tool functions.
**Files**: `tests/test_tools_challenge.py`, `tests/test_tools_seed_image.py`, `tests/test_tools_narrator.py`, `tests/test_tools_illustrator.py`, `tests/test_tools_pdf.py`
**Acceptance Criteria**:
- Test each tool's success path with valid inputs
- Test error handling with invalid inputs
- Test ToolResponse structure and typing
- Mock external API calls (OpenAI, Google)
- Achieve >80% code coverage for tools
- Use pytest framework
- Add `pytest>=8.0.0` and `pytest-cov` to dev dependencies
**Dependencies**: 2.2, 2.3, 2.4, 2.5, 2.6
**Notes**: Tools are critical business logic - they need comprehensive testing.

### 5.2 Integration Tests for Workflow
**Status**: TODO
**Description**: Create end-to-end integration tests for the complete book creation workflow.
**Files**: `tests/test_workflow_integration.py`
**Acceptance Criteria**:
- Test complete workflow from challenge discovery to PDF generation
- Test workflow state transitions
- Test approval mechanism
- Test error recovery
- Test session isolation (multiple concurrent sessions)
- Use test fixtures for sample data
- Mock external API calls but test actual integration logic
**Dependencies**: 1.5, 3.3, 3.4, 3.5, 3.6
**Notes**: Integration tests ensure the workflow pieces work together correctly.

### 5.3 Agent Behavior Testing
**Status**: TODO
**Description**: Test agent conversation flow and decision-making.
**Files**: `tests/test_agent_behavior.py`
**Acceptance Criteria**:
- Test that agent follows correct tool calling sequence
- Test that agent asks for approvals at correct times
- Test that agent handles parent rejections/change requests
- Test that agent ends conversation after PDF approval
- Test that agent prevents out-of-order operations
- Use LangChain testing utilities
**Dependencies**: 3.2, 3.3, 3.4, 3.5, 3.6
**Notes**: Agent behavior is complex and needs careful testing. Consider using prompt testing frameworks.

### 5.4 UI Testing
**Status**: TODO
**Description**: Create tests for Streamlit UI components.
**Files**: `tests/test_ui.py`
**Acceptance Criteria**:
- Test session state initialization
- Test message rendering
- Test file upload handling
- Test workflow progress indicator updates
- Test book preview rendering
- Use Streamlit testing utilities
**Dependencies**: 4.2, 4.3, 4.4, 4.5, 4.6
**Notes**: UI testing in Streamlit can be challenging - focus on component logic rather than rendering.

### 5.5 Example Data and Demo Mode
**Status**: TODO
**Description**: Create example data and a demo mode for testing and demonstrations.
**Files**: `src/demo/sample_data.py`, `src/core/settings.py`
**Acceptance Criteria**:
- Create sample ChallengeData for common scenarios (fear of dark, starting school, new sibling)
- Create sample child images (stock photos or generated)
- Create sample book content
- Add `demo_mode` flag to settings
- In demo mode, use cached/sample data instead of calling expensive APIs
- Add "Load Demo Book" button in UI when in demo mode
**Dependencies**: 1.6
**Notes**: Demo mode is useful for development, testing, and showing the app without incurring API costs.

### 5.6 Documentation
**Status**: TODO
**Description**: Create comprehensive documentation for the project.
**Files**: `README.md`, `docs/USER_GUIDE.md`, `docs/DEVELOPER_GUIDE.md`, `docs/API.md`
**Acceptance Criteria**:
- Update README.md with:
  - Project description and goals
  - Installation instructions
  - Environment setup
  - Quick start guide
  - Screenshots/demo
- Create USER_GUIDE.md:
  - How to use the app
  - Workflow explanation
  - Tips for best results
  - FAQ
  - Troubleshooting
- Create DEVELOPER_GUIDE.md:
  - Architecture overview
  - Code structure
  - Adding new tools
  - Testing guide
  - Contribution guidelines
- Create API.md:
  - All Pydantic models
  - All tool function signatures
  - Workflow state schema
  - Settings configuration
**Dependencies**: All previous tasks
**Notes**: Good documentation is essential for maintainability and user adoption.

### 5.7 Deployment Configuration
**Status**: TODO
**Description**: Create deployment configuration for production environment.
**Files**: `Dockerfile`, `.streamlit/config.toml`, `docker-compose.yml`, `requirements.txt`
**Acceptance Criteria**:
- Create Dockerfile for containerization
- Create `.streamlit/config.toml` for Streamlit configuration
- Create docker-compose.yml for easy deployment
- Generate requirements.txt from pyproject.toml
- Add health check endpoint
- Configure environment variable handling for production
- Add instructions for deploying to common platforms (Streamlit Cloud, AWS, GCP, Heroku)
**Dependencies**: All previous tasks
**Notes**: Consider using Docker for consistent deployment across environments.

### 5.8 Performance Optimization
**Status**: TODO
**Description**: Optimize performance for production use, especially for API calls and image processing.
**Files**: `src/ai/agent.py`, `src/ai/tools/*.py`, `src/core/cache.py`
**Acceptance Criteria**:
- Implement caching for LLM responses (same inputs should return cached results)
- Optimize image processing (compression, resizing)
- Implement request batching where possible
- Add rate limiting for API calls
- Monitor and log API costs per session
- Add timeout handling for long-running operations
- Create `CacheManager` class for managing cached results
- Add cost estimation before starting workflow
**Dependencies**: 2.2, 2.3, 2.4, 2.5, 2.6
**Notes**: LLM and image generation APIs are expensive - caching and optimization are important for cost control.

### 5.9 Security and Privacy
**Status**: TODO
**Description**: Implement security measures and privacy protections for user data.
**Files**: `src/core/security.py`, `src/core/settings.py`, `docs/PRIVACY.md`
**Acceptance Criteria**:
- Implement secure file upload validation (file type, size, content scanning)
- Add API key rotation mechanism
- Ensure uploaded photos are deleted after session ends (or after configurable retention period)
- Encrypt sensitive data in database
- Add GDPR-compliant data handling
- Create privacy policy document
- Add option for users to delete all their data
- Log security events (failed uploads, suspicious activity)
- Add rate limiting to prevent abuse
**Dependencies**: 1.4, 4.6
**Notes**: User trust is critical, especially when handling children's photos. Privacy and security should be top priorities.

### 5.10 Monitoring and Analytics
**Status**: TODO
**Description**: Add monitoring, analytics, and observability for production system.
**Files**: `src/core/monitoring.py`, `src/core/analytics.py`
**Acceptance Criteria**:
- Implement application metrics:
  - Sessions started/completed
  - Workflow step completion rates
  - Tool success/failure rates
  - Average time per workflow step
  - API costs per session
- Add error tracking and alerting
- Implement structured logging for all components
- Add health check endpoints
- Create dashboard for monitoring (optional: use Grafana/Prometheus)
- Track user satisfaction (optional survey after PDF generation)
**Dependencies**: All previous tasks
**Notes**: Monitoring helps identify issues and optimize the user experience. Start simple and expand over time.

---

## Summary

**Total Tasks**: 49
**Completed (DONE)**: 5
**Remaining (TODO)**: 44

### Critical Path (Priority Order)
1. **Infrastructure**: 1.5, 1.6 (workflow state and data models are foundational)
2. **Tools**: 2.2 → 2.3 → 2.4 → 2.5 → 2.6 (in sequence, as they depend on each other)
3. **Orchestration**: 3.2 → 3.3 → 3.4 → 3.5 → 3.6 (agent must understand and execute workflow)
4. **UI**: 4.2, 4.3, 4.4 (improve user experience)
5. **QA & Deployment**: 5.1, 5.2, 5.3 (ensure quality before production)

### Quick Start Recommendation
To get a working MVP as quickly as possible, focus on this minimal set:
1. 1.5 (Workflow State Management)
2. 1.6 (Data Models)
3. 2.2 (Challenge Discovery)
4. 2.3 (Seed Image Generator)
5. 2.4 (Narrator)
6. 2.5 (Illustrator)
7. 2.6 (PDF Generator)
8. 3.2 (Workflow-Aware System Prompt)
9. 3.3 (Workflow State Integration)
10. 3.4 (Tool Registration)

This creates a complete (if basic) book creation pipeline. Then add approvals (3.5), termination logic (3.6), and UI improvements (4.2-4.4) for better UX.
