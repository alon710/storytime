# 📚 StoryTime - AI-Powered Children's Storybook Generator

Create beautifully illustrated children's storybooks with custom AI-generated images. StoryTime uses Google's Gemini 2.5 Flash Image Preview to generate consistent character illustrations based on your prompts.

## ✨ Features

- **Dynamic Page Creation**: Add and remove pages as needed for your story
- **Custom Illustration Prompts**: Describe exactly what you want to see in each illustration
- **Character Consistency**: Upload a character photo to maintain visual consistency across all pages
- **Image-Only PDF Output**: Generate clean PDFs with illustrations only (no text)
- **Multiple Art Styles**: Choose from storybook, watercolor, or cartoon styles
- **Character Customization**: Set character name, age, and gender for age-appropriate illustrations

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- Google Gemini API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd storytime
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Set up your environment**:
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   MODEL=gemini-2.5-flash-image-preview
   ```

4. **Get your Google API key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add it to your `.env` file

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 How to Use

### 1. Book Settings
- **Book Title**: Enter the title for your storybook
- **Character Photo**: Upload an image of your character (JPG, JPEG, or PNG)
- **Character Name**: Enter the character's name
- **Age**: Set the character's age (1-12 years)
- **Gender**: Select Boy or Girl for character consistency
- **Art Style**: Choose from:
  - **Storybook**: Classic children's book illustration style
  - **Watercolor**: Soft, painted watercolor effects
  - **Cartoon**: Bold, animated cartoon style

### 2. Create Your Story Pages
- Click **"➕ Add Page"** to add new pages to your story
- Click **"➖ Remove Page"** to remove the last page
- For each page, provide:
  - **Page Title**: A descriptive title for the page
  - **Story Text**: Context text (helps with illustration but won't appear in PDF)
  - **Illustration Prompt**: Detailed description of what you want to see in the illustration

### 3. Generate Your Storybook
- Click **"🎨 Generate Illustrated Storybook"**
- Wait for the AI to generate illustrations for each page
- Download your completed PDF storybook

## 💡 Tips for Better Illustrations

### Writing Effective Prompts
- **Be specific**: Instead of "Alex playing", write "Alex playing with a red ball in a sunny park"
- **Include setting details**: "Alex in a cozy bedroom with toys scattered on the floor"
- **Describe emotions**: "Alex looking excited and happy while opening a gift"
- **Add environmental context**: "Alex walking through a magical forest with tall trees and butterflies"

### Example Prompts
```
Page 1: Alex standing at the entrance of a mysterious cave, holding a flashlight, looking curious and adventurous

Page 2: Alex discovering a hidden treasure chest glowing with golden light in the depths of the cave

Page 3: Alex running home excitedly through a meadow, carrying a small treasure, with the sun setting behind rolling hills
```

## 🛠️ Technical Details

### Dependencies
- **Streamlit**: Web application framework
- **Google GenAI**: AI image generation
- **Pillow**: Image processing
- **ReportLab**: PDF generation
- **Pydantic**: Configuration management

### Project Structure
```
storytime/
├── app.py                 # Main Streamlit application
├── story_processor.py     # Core image generation and PDF creation logic
├── config.py             # Configuration settings
├── pyproject.toml        # Project dependencies and metadata
├── .env                  # Environment variables (you create this)
└── README.md            # This file
```

### Image Generation Process
1. **Character Reference**: Uses uploaded character photo for consistency
2. **Custom Prompts**: Processes your illustration descriptions
3. **AI Generation**: Calls Google Gemini 2.5 Flash Image Preview
4. **Style Consistency**: Maintains same art style and character appearance across all pages
5. **PDF Creation**: Generates image-only PDF with titles

## 🔧 Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Your Google Gemini API key (required)
- `MODEL`: Model name (default: `gemini-2.5-flash-image-preview`)

### Supported File Formats
- **Character Images**: JPG, JPEG, PNG
- **Output**: PDF

## 🚨 Troubleshooting

### Common Issues

**"Please set your GOOGLE_API_KEY"**
- Ensure your `.env` file exists in the project root
- Verify your API key is valid and active

**"Image generation failed"**
- Check your internet connection
- Verify your Google API key has sufficient quota
- Ensure your prompts are appropriate and clear

**"No text or words in the illustration"**
- This is intentional - the app generates image-only PDFs
- Text context is used for AI understanding but doesn't appear in output

### Performance Tips
- Shorter illustration prompts may generate faster
- Complex scenes with many elements may take longer
- Consider generating 3-5 pages for optimal processing time

## 📝 License

This project is open source. Feel free to modify and distribute as needed.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 💬 Support

For issues, questions, or feature requests, please open an issue in the repository.

---

**Happy storytelling! 📖✨**