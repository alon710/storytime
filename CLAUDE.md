# StoryTime Project Rules for Claude

## 🔄 IMPORTANT: Update This File After Every Change
**Always update this CLAUDE.md file when making changes to project structure, patterns, conventions, or adding new dependencies. This ensures accurate guidance for future development.**

---

## Project Overview

StoryTime is an AI-powered children's book illustration generator built with Streamlit and Google Gemini AI. The application creates personalized children's stories with custom illustrations based on user-provided character references and story templates.

**Core Features:**
- Personalized story generation with character customization
- AI-generated illustrations using Google Gemini
- Template-based story structure with editing capabilities
- Multi-language support (English/Hebrew)
- Multiple art styles (watercolor, cartoon, Ghibli, digital, Pixar, vintage)
- PDF export and download functionality

---

## Architecture & Project Structure

```
app/
├── __init__.py
├── ai/
│   ├── base.py
│   ├── image_generator.py
│   ├── story_processor.py
│   ├── text_processor.py
│   └── templates/
├── ui/
│   ├── components/
│   └── pages/
├── utils/
│   ├── schemas.py
│   ├── settings.py
│   ├── logger.py
│   ├── temp_file.py
│   ├── download_manager.py
│   └── utils.py
└── story_templates/
```

---

## Dependencies & Technologies

### Core Technologies
- **Python 3.12+** - Required minimum version
- **Streamlit >= 1.40.0** - Web framework for UI
- **Google GenAI >= 0.8.0** - Google Gemini AI integration
- **Pydantic >= 2.5.0** - Data validation and settings
- **Pillow >= 10.0.0** - Image processing
- **Jinja2 >= 3.1.6** - Template engine for AI prompts
- **structlog >= 25.4.0** - Structured logging

### Development Tools
- **uv** - Package management (preferred over pip)
- **pyproject.toml** - Project configuration
- **pytest >= 8.0.0** - Testing framework
- **pytest-cov >= 5.0.0** - Code coverage reporting
- **pytest-asyncio >= 0.24.0** - Async testing support
- **pytest-mock >= 3.14.0** - Mocking utilities
- **Ruff** - Fast Python linter and formatter
- **Type checking** - Using `ty check` via uvx

---

## Coding Conventions

### General Python Standards
- **Type hints are mandatory** for all function parameters and return values
- **PEP 8 compliance** for formatting and naming
- **NO COMMENTS OR DOCSTRINGS** - Code must be self-documenting through clear naming
- **Use f-strings** for string formatting

### Code Documentation Rules
- **NEVER add comments** to code under any circumstances
- **NEVER add docstrings** to functions, classes, or methods
- **Remove existing comments/docstrings** when editing code
- **Self-documenting code** through descriptive variable and function names
- **Clear structure** and logical organization instead of explanatory text

### Import Organization
```python
import io
from typing import Optional, List
from pathlib import Path

import streamlit as st
from pydantic import BaseModel
from google import genai

from app.utils.schemas import StoryMetadata
from app.utils.logger import logger
```

### Naming Conventions
- **Classes**: PascalCase (`StoryProcessor`, `MetadataManager`)
- **Functions/Methods**: snake_case (`generate_story`, `render_metadata_step`)
- **Variables**: snake_case (`character_name`, `art_style`)
- **Constants**: UPPER_SNAKE_CASE (`ART_STYLE_DESCRIPTIONS`, `SESSION_STATE_KEYS`)
- **Enums**: PascalCase class, snake_case values (`Gender.boy`, `ArtStyle.watercolor`)

### File Organization
- **One class per file** when possible
- **Static methods** for utility functions within classes
- **Module-level functions** for standalone utilities
- **Separate concerns**: UI components, business logic, and data models

---

## Design Patterns

### Pydantic Models for Data Validation
```python
class StoryMetadata(BaseModel):
    character_name: str
    age: int
    gender: Gender
    language: Language = Language.english
    art_style: ArtStyle = ArtStyle.watercolor
    instructions: Optional[str] = None
```

### Enum Usage for Controlled Values
```python
class Gender(str, Enum):
    boy = "Boy"
    girl = "Girl"
```

### Static Method Classes for Components
```python
class MetadataManager:
    @staticmethod
    def render() -> Optional[StoryMetadata]:
        pass
```

### Abstract Base Classes for AI Components
```python
class BaseAIGenerator(ABC):
    def __init__(self, client: genai.Client, model: str):
        self.client = client
        self.model = model

    @abstractmethod
    def generate(self, *args, **kwargs):
        pass
```

---

## AI Integration Guidelines

### Google Gemini Integration Patterns

#### Client Initialization
```python
def __init__(self):
    client = genai.Client(api_key=settings.google_api_key)
    model = settings.model
    self.image_generator = ImageGenerator(client=client, model=model)
```

#### Generation Configuration
```python
generation_config = types.GenerateContentConfig(
    temperature=0.4,
    top_p=1,
    top_k=32,
    max_output_tokens=8192,
    response_modalities=["Text", "Image"],
)
```

#### Template-Based Prompts
- Use **Jinja2 templates** in `app/ai/templates/` for all AI prompts
- Template naming: `{purpose}.j2` (e.g., `image_generation.j2`)
- Load templates using Environment with FileSystemLoader

#### Error Handling for AI Calls
```python
try:
    response = self._generate_content(contents, config=generation_config)
    if not response or not response.candidates:
        logger.warning("No response from AI")
        return None
    return self._process_response(response)
except Exception as e:
    logger.error(f"AI generation failed: {str(e)}")
    return None
```

---

## UI/UX Guidelines

### Streamlit Component Patterns

#### Session State Management
```python
class SessionStateKeys:
    METADATA = "metadata"
    SEED_IMAGES = "seed_images"
```

#### Component Structure
```python
@staticmethod
def render() -> Optional[DataType]:
    initialize_session_state()
    render_ui_elements()
    update_session_state()
    return process_data()
```

#### User Input Validation
```python
character_name = st.text_input(
    "Character Name",
    placeholder="e.g., Alice, Tom",
    key=SessionStateKeys.CHAR_NAME,
    help="Descriptive help text",
)
```

#### Progress Indicators
```python
with st.spinner("Generating your story..."):
    result = perform_generation()
```

#### Error Display
```python
if not metadata:
    st.warning("Please complete Step 1 first.")
    return

try:
    result = perform_operation()
except Exception as e:
    st.error(f"Error: {str(e)}")
```

---

## Error Handling & Logging

### Logging Standards
```python
from app.utils.logger import logger

logger.info("Processing page", page_number=1, title="Adventure")
logger.warning("No response from AI", classname=self.__class__.__name__)
logger.error(f"Generation failed: {str(e)}")
```

### Exception Handling Patterns
```python
try:
    result = process_data()
    return result
except SpecificException as e:
    logger.error(f"Specific error: {str(e)}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    logger.error(traceback.format_exc())
    return None
```

### Graceful Degradation
- **Always provide fallbacks** for AI failures
- **Return None or empty collections** rather than raising exceptions in UI components
- **Use optional types** to indicate possible failure states

---

## Configuration Management

### Multi-Model Settings Pattern
The application now supports different Google Gemini models for different AI tasks, allowing for optimization of performance, cost, and quality based on the specific use case.

```python
# app/utils/settings.py
class Settings(BaseSettings):
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")

    seed_image_model: str = Field(
        default="gemini-2.0-flash-exp",
        env="SEED_IMAGE_MODEL",
        description="Model used for generating character reference images from photos"
    )
    story_text_model: str = Field(
        default="gemini-2.0-flash-exp",
        env="STORY_TEXT_MODEL",
        description="Model used for text personalization and story processing"
    )
    story_image_model: str = Field(
        default="gemini-2.5-flash-image-preview",
        env="STORY_IMAGE_MODEL",
        description="Model used for generating story illustrations"
    )
    default_model: str = Field(
        default="gemini-2.5-flash-image-preview",
        env="DEFAULT_MODEL",
        description="Fallback model for backward compatibility"
    )

    model: str = Field(
        default="gemini-2.5-flash-image-preview",
        env="MODEL",
        description="Legacy model field - use specific model fields instead"
    )

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
```

### Model Configuration Guidelines

#### Model Selection Strategy
- **seed_image_model**: Used for character reference generation from uploaded photos
  - Recommended: `gemini-2.0-flash-exp` for fast processing
  - Alternative: `gemini-2.5-flash-image-preview` for higher quality

- **story_text_model**: Used for text personalization and story processing
  - Recommended: `gemini-2.0-flash-exp` for JSON schema support and speed
  - Alternative: `gemini-1.5-pro` for complex narrative structures

- **story_image_model**: Used for generating story illustrations
  - Recommended: `gemini-2.5-flash-image-preview` for best image quality
  - Alternative: `gemini-2.0-flash-exp` for faster generation

#### Performance vs Quality Trade-offs
- **Fast Generation**: Use `gemini-2.0-flash-exp` for all models
- **Balanced**: Use defaults (flash-exp for text/seed, flash-image-preview for stories)
- **High Quality**: Use `gemini-2.5-flash-image-preview` for all models
- **Cost Optimization**: Use smaller/faster models for less critical tasks

### Environment Variables
- Use `.env` file for local development with specific model configurations
- Provide `.env.example` with all required variables and recommended configurations
- Use `pydantic-settings` for configuration management with field descriptions
- Support legacy `MODEL` environment variable for backward compatibility

### Example Environment Configuration
```env
# Multi-model configuration
SEED_IMAGE_MODEL=gemini-2.0-flash-exp
STORY_TEXT_MODEL=gemini-2.0-flash-exp
STORY_IMAGE_MODEL=gemini-2.5-flash-image-preview
DEFAULT_MODEL=gemini-2.5-flash-image-preview

# Legacy model (optional, deprecated)
MODEL=gemini-2.5-flash-image-preview
```

---

## Story Template Structure

### JSON Template Format
```json
{
  "name": "Template Name",
  "description": "Brief description",
  "default_title": "Story Title",
  "pages": [
    {
      "title": "Page Title",
      "story_text": "Story content with placeholders like Hero",
      "illustration_prompt": "Detailed prompt for image generation"
    }
  ]
}
```

### Template Guidelines
- Use **"Hero"** as placeholder for character name
- Include **detailed illustration prompts**
- Keep story text **age-appropriate and simple**
- Structure as sequential pages building a narrative

---

## Image Processing Standards

### Image Handling
```python
target_size = 800
image.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

final_image = Image.new("RGB", (target_size, target_size), (255, 255, 255))
```

### Temporary File Management
```python
from app.utils.temp_file import save_image_to_temp

temp_path = save_image_to_temp(image=final_image, suffix=Suffix.png)
```

---

## Testing Infrastructure

### Test Configuration
The project uses **pytest** with comprehensive configuration in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=70
```

### Test Structure
```
tests/
├── conftest.py
├── ai/
│   ├── test_base.py
│   ├── test_image_generator.py
│   ├── test_story_processor.py
│   └── test_text_processor.py
├── test_download_manager.py
├── test_schemas.py
├── test_settings.py
└── test_utils.py
```

### Test Fixtures & Mocking

#### Shared Fixtures in conftest.py
```python
@pytest.fixture
def mock_genai_client():
    client = MagicMock()
    response = MagicMock()
    response.candidates = [MagicMock()]
    response.candidates[0].content.parts = [MagicMock()]
    response.candidates[0].content.parts[0].text = "Generated content"
    client.models.generate_content.return_value = response
    return client

@pytest.fixture
def sample_metadata():
    return StoryMetadata(
        character_name="Alice",
        age=7,
        gender=Gender.girl,
        language=Language.english,
        art_style=ArtStyle.watercolor,
        instructions="Make it magical and fun",
    )
```

#### Streamlit Mocking
```python
@pytest.fixture
def mock_streamlit():
    with patch("streamlit.session_state", {}):
        with patch("streamlit.write") as mock_write:
            with patch("streamlit.error") as mock_error:
                yield {
                    "write": mock_write,
                    "error": mock_error,
                    "success": mock_success,
                }
```

### Test Categories & Markers

#### Pytest Markers
- **unit**: Unit tests for individual components
- **integration**: Integration tests across modules
- **slow**: Tests that take longer to execute
- **requires_api**: Tests that require actual API keys

#### Usage Examples
```python
@pytest.mark.unit
def test_story_metadata_validation():
    pass

@pytest.mark.integration
@pytest.mark.requires_api
def test_full_story_generation():
    pass
```

### Testing Patterns

#### Mock AI API Calls
```python
@patch("app.ai.story_processor.settings")
@patch("app.ai.story_processor.genai.Client")
def test_generate_story_success(
    self, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
):
    mock_settings.google_api_key = "test-key"
    mock_settings.model = "test-model"

    processor = StoryProcessor()

    with patch.object(processor.text_processor, "process_pages") as mock_text:
        mock_text.return_value = {0: "Processed text"}

        result = processor.generate_story(
            story_template=sample_story_template,
            metadata=sample_metadata,
        )
```

#### Environment Variable Mocking
```python
@pytest.fixture
def mock_env_vars():
    env_vars = {
        "GOOGLE_API_KEY": "test-api-key",
        "MODEL": "test-model",
        "LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars
```

#### File System Mocking
```python
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_image_file(temp_dir: Path) -> Path:
    from PIL import Image

    image_path = temp_dir / "test_image.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(image_path)
    return image_path
```

### Code Coverage Requirements
- **Minimum coverage**: 70% (enforced by pytest configuration)
- **Coverage reports**: Generated in terminal, HTML, and XML formats
- **Coverage scope**: All modules under `app/` directory

### Testing Commands
```bash
# Run all tests with coverage
uv run pytest tests/ --cov=app --cov-report=term-missing -v

# Run specific test categories
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m "not slow"

# Run tests with detailed output
uv run pytest tests/ -v --tb=long
```

---

## GitHub Actions CI/CD Pipeline

### Workflow Overview
The CI/CD pipeline is defined in `.github/workflows/ci.yml` with three main jobs:

#### 1. Lint and Type Check Job
```yaml
lint-and-type-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - name: Install uv
      uses: astral-sh/setup-uv@v3
    - name: Install dependencies
      run: uv sync --all-groups --frozen
    - name: Run Ruff linter
      run: uvx ruff check . --fix --unsafe-fixes
    - name: Run type checker
      run: uvx ty check
```

#### 2. Test Job
```yaml
test:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ['3.12']
  steps:
    - name: Run tests with coverage
      run: |
        uv run pytest tests/ \
          --cov=app \
          --cov-report=term-missing \
          --cov-report=xml \
          --cov-report=html \
          -v
    - name: Upload coverage reports
      uses: actions/upload-artifact@v4
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
```

#### 3. Streamlit Verification Job
```yaml
verify-streamlit:
  runs-on: ubuntu-latest
  steps:
    - name: Test Streamlit import
      run: |
        uv run python -c "import streamlit; import app; print('Streamlit app imports successfully')"
    - name: Check Streamlit syntax
      run: |
        uv run python -m py_compile app.py
        find app -name "*.py" -exec uv run python -m py_compile {} \;
```

### CI/CD Features

#### Caching Strategy
- **uv dependency caching** with `cache-dependency-glob: "uv.lock"`
- **Automatic cache invalidation** when dependencies change

#### Environment Setup
- **Python 3.12** as the target version
- **uv package manager** for fast dependency installation
- **Test environment variables** automatically configured

#### Quality Gates
- **Linting** with Ruff (with auto-fixes applied)
- **Type checking** with `ty check`
- **Test coverage** reporting with minimum thresholds
- **Streamlit syntax validation**

#### Artifact Management
- **Coverage reports** uploaded as build artifacts
- **HTML coverage reports** for detailed analysis
- **Codecov integration** for coverage tracking

### Trigger Conditions
```yaml
on:
  push:
    branches: [main, refactor]
  pull_request:
    branches: [main, refactor]
```

### Environment Variables in CI
```yaml
env:
  GOOGLE_API_KEY: test-key
  MODEL: test-model
```

---

## Testing & Quality Standards

### Code Quality Requirements
- **Type checking** with `ty check` (part of CI pipeline)
- **Linting** with Ruff (auto-fixes applied in CI)
- **Import sorting** and formatting consistency
- **Error handling** for all external API calls
- **Logging** for all significant operations
- **Minimum 70% code coverage** (enforced)

### Testing Guidelines

#### Test Organization
- **One test file per module** following `test_*.py` naming
- **Test classes** for grouping related tests
- **Descriptive test names** explaining what is being tested

#### Mock Strategy
- **Mock all external dependencies** (Google GenAI, file systems)
- **Use fixtures** for consistent test data
- **Mock environment variables** for configuration testing
- **Mock Streamlit** components for UI testing

#### Test Categories
- **Unit tests** for individual functions and methods
- **Integration tests** for module interactions
- **Error scenario testing** for failure conditions
- **Data validation testing** for Pydantic models

#### Best Practices
- **Test both success and failure paths**
- **Use parameterized tests** for multiple input scenarios
- **Test edge cases** and boundary conditions
- **Verify logging output** where appropriate
- **Clean up resources** in test teardown

---

## Performance Guidelines

### AI API Optimization
- **Reuse clients** instead of creating new ones
- **Batch operations** when possible
- **Implement timeouts** for long-running operations
- **Cache results** when appropriate (especially for templates)

### Image Processing
- **Consistent image sizes** (800x800 for generated images)
- **Optimize file formats** (PNG for generated, JPEG for uploads)
- **Clean up temporary files** after use

---

## Security Guidelines

### API Key Management
- **Never hardcode API keys** in source code
- **Use environment variables** for all secrets
- **Validate API responses** before processing
- **Log security-relevant events** appropriately

### File Handling
- **Validate uploaded file types** and sizes
- **Use temporary files** for processing
- **Clean up files** after processing
- **Sanitize file names** for downloads

---

## Important Development Rules

### 🚨 Critical Guidelines

1. **Always update CLAUDE.md** when changing project structure or patterns
2. **NEVER write comments or docstrings** - code must be self-documenting through clear naming
3. **Remove existing comments/docstrings** when editing any code
4. **Use type hints** for all function parameters and return values
5. **Handle AI API failures gracefully** - never let them crash the UI
6. **Log all significant operations** with appropriate context
7. **Follow the established session state patterns** for UI components
8. **Use Pydantic models** for all data validation
9. **Implement proper error handling** with user-friendly messages
10. **Test AI integrations** with mock responses during development
11. **Keep templates and prompts** separate from code logic
12. **Follow the established file organization** patterns
13. **Use multi-model configuration** - leverage specific models for different AI tasks
14. **Configure model selection** based on performance, cost, and quality requirements
15. **Write tests for all new functionality** with minimum 70% coverage
16. **Run tests locally** before pushing changes (`uv run pytest`)
17. **Mock external dependencies** in tests (AI APIs, file systems)
18. **Use GitHub Actions CI** to validate all changes

### 🔧 Development Workflow

1. **Check existing patterns** before implementing new features
2. **Update schemas** when adding new data structures
3. **Add logging** for new operations
4. **Write tests** for new functionality with appropriate fixtures
5. **Run linting and type checking** locally (`uvx ruff check`, `uvx ty check`)
6. **Test error scenarios** thoroughly with mocked failures
7. **Verify CI passes** before merging PRs
8. **Update this file** when adding new patterns or changing existing ones

### 🧪 Testing Workflow

1. **Write tests alongside implementation** - don't leave testing for later
2. **Use existing fixtures** from `conftest.py` when possible
3. **Mock external dependencies** consistently
4. **Test both success and failure paths**
5. **Run tests locally** before committing (`uv run pytest tests/`)
6. **Check coverage** and aim for high coverage of new code
7. **Use appropriate test markers** for categorization

### 📝 Documentation Standards

- **Self-documenting code** through descriptive names and clear structure
- **Document configuration options** in settings with field descriptions
- **Use README and CLAUDE.md** for high-level architecture documentation
- **Avoid inline documentation** - let code structure tell the story

---

## Common Gotchas & Solutions

### Streamlit Session State
- **Initialize all session state keys** in dedicated methods
- **Use SessionStateKeys constants** instead of magic strings
- **Update related keys** when updating complex objects

### AI Response Handling
- **Always check for None responses** from AI calls
- **Handle missing image data** in AI responses
- **Provide fallback content** when AI fails

### Image Processing
- **Convert images to RGB** before saving as JPEG
- **Handle different input image formats** consistently
- **Maintain aspect ratios** during resizing

---

*Last updated: September 2024 - Added multi-model configuration system and strict no-comments/no-docstrings rules - Remember to update this section when modifying the file!*