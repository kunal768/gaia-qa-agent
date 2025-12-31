# HuggingFace Agents Course - Final Assignment Solution

A robust CLI-based AI agent solution for the HuggingFace Agents Course Unit 4 final assignment. This agent successfully handles diverse tasks including web searches, image analysis, audio transcription, code execution, and data processing.

## 🎯 Features

- **Multi-modal Capabilities**: Handles text, images, audio, code, and spreadsheet files
- **CLI Interface**: Clean command-line interface for easy execution
- **Answer Caching**: Saves progress after each question - resume anytime
- **Timeout Protection**: 5-minute timeout per question to prevent hanging
- **Smart Question Detection**: Automatically detects and enhances different question types
- **Error Handling**: Robust error handling with detailed logging

## 🛠️ Tech Stack

- **Model**: GPT-4o (OpenAI)
- **Framework**: smolagents
- **Tools**: 
  - DuckDuckGoSearchTool (web search)
  - VisitWebpageTool (web page access)
  - PythonInterpreterTool (code execution)
  - SpeechToTextTool (audio transcription)

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Hugging Face account (for authentication)

## 🚀 Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Final_Assignment_Template
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
# Create a .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

4. Login to Hugging Face:
```bash
huggingface-cli login
```

## 💻 Usage

### Process Questions (Cache Answers)
Process all questions and save answers to cache:
```bash
python app.py --process
```

### Submit Cached Answers
Submit previously cached answers:
```bash
python app.py --submit
```

### Process and Submit in One Go
Process questions and submit immediately:
```bash
python app.py --process-and-submit
```

## 📊 How It Works

The agent uses intelligent question type detection to enhance prompts:

1. **Reversed Text**: Automatically detects and reverses text
2. **YouTube Videos**: Uses web search and page access tools
3. **Images/Chess**: Provides PIL/Pillow instructions for image analysis
4. **Audio Files**: Uses SpeechToTextTool for transcription
5. **Python Code**: Reads and executes code files
6. **Excel/CSV**: Uses pandas for data analysis
7. **Mathematical Problems**: Uses Python for step-by-step computation
8. **Research Questions**: Uses web search with iterative refinement

## 📁 Project Structure

```
.
├── app.py                 # Main CLI application
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── .env                  # Environment variables (not in repo)
└── agent_answers_cache.json  # Cached answers (not in repo)
```

## 🔒 Security

- `.env` file is gitignored - never commit API keys
- Cache files are excluded from version control
- All sensitive data is kept local

## 📝 Notes

- Answers are cached after each question for resilience
- The agent has a 5-minute timeout per question
- Progress is displayed in real-time during processing
- You can stop and resume processing anytime

## 🎓 Course Information

This project was developed for the **HuggingFace Agents Course - Unit 4 Final Assignment**.

## 📄 License

This project is for educational purposes as part of the HuggingFace Agents Course.

## 🙏 Acknowledgments

- HuggingFace for the excellent Agents Course
- smolagents framework
- OpenAI for GPT-4o
