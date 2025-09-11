# 📚 StoryTime - AI Story Book Generator

Transform your PDF stories into beautiful illustrated children's books using **Gemini 2.5 Flash Image Preview** (nano-banana) - Google's latest AI model for image generation.

## ✨ Features

- **PDF Story Processing**: Extract text from PDF files and convert to story pages
- **Nano-Banana Image Generation**: Use Gemini 2.5 Flash Image Preview for actual image generation
- **Character Consistency**: Maintain visual consistency by passing character reference image directly
- **Multiple Art Styles**: Choose from Storybook, Watercolor, Cartoon styles
- **Professional PDF Output**: Generate print-ready PDF booklets with proper layout
- **Fail-Fast Architecture**: Clear error messages if image generation fails
- **Simple Interface**: Clean Streamlit web interface (90 lines total)

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Google API key for Gemini ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd storytime
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add: GOOGLE_API_KEY=your_google_api_key_here
   ```

4. **Run the application**
   ```bash
   uv run streamlit run app.py
   ```

5. **Open your browser**
   - Open http://localhost:8501

## 📖 How to Use

1. **Upload Files**
   - Upload a PDF containing your story text
   - Upload a photo of your character (baby/child)

2. **Configure Story**
   - Enter character name and age
   - Choose art style
   - Set maximum pages to process
   - Choose output folder

3. **Generate**
   - Click "Generate Storybook"
   - Watch real-time progress
   - Download your completed PDF booklet

## 🎨 Art Styles

- **📄 Paper Cutout**: Layered paper craft style with clean edges and dimensional depth
- **⚡ Minimalist**: Simple, clean designs with flat colors and geometric shapes  
- **🎨 Watercolor**: Soft, flowing colors with gentle brushstrokes and texture
- **🎭 Cartoon**: Bright, playful illustrations with bold colors and simple shapes
- **📚 Classic Storybook**: Traditional children's book style with warm, inviting colors

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with:

```bash
# Required
OPENROUTER_API_KEY=your_api_key_here
```

## 📁 Clean Project Structure

```
storytime/
├── app.py                 # Main Streamlit app (90 lines)
├── story_processor.py     # Core processing with nano-banana (180 lines)  
├── config.py             # Simple Pydantic settings (25 lines)
├── pyproject.toml        # UV dependencies (minimal)
├── .env.example          # Environment template
└── README.md            # This documentation
```

## 🔧 Troubleshooting

### Common Issues

1. **Missing API Key**
   - Ensure `GOOGLE_API_KEY` is set in your .env file
   - Get a valid API key from https://makersuite.google.com/app/apikey

2. **Image Generation Fails**
   - App will show clear error: "Image generation not supported with current model"
   - This is expected behavior - app fails fast instead of creating text-only books
   - Verify your Google API key has access to Gemini 2.5 Flash Image Preview

3. **File Upload Errors**
   - Ensure PDF contains readable text
   - Verify image format (JPG, PNG)

4. **Slow Processing** 
   - Each image takes 3-5 seconds with nano-banana
   - Large PDFs take longer to process
   - Consider reducing max_pages for faster results

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenRouter for AI model API access
- Streamlit for the web interface framework
- ReportLab for PDF generation

## 📞 Support

For issues and questions:
1. Check this README for common solutions
2. Open an issue on GitHub

---

**StoryTime** - Making every child the hero of their own illustrated adventure! 📚✨