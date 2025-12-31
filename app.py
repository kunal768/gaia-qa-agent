import os
import requests
import pandas as pd
import tempfile
import json
import sys
import argparse
import time
import threading
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# --- Constants ---
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"
CACHE_FILE = "agent_answers_cache.json"

from smolagents import (
    CodeAgent, 
    OpenAIModel, 
    Tool, 
    DuckDuckGoSearchTool, 
    VisitWebpageTool,
    PythonInterpreterTool,
    SpeechToTextTool
)

class BasicAgent:
    def __init__(self):
        # Use gpt-4o for better performance on complex tasks
        self.model = OpenAIModel(model_id="gpt-4o")
        # Add more tools for better task handling
        self.tools = [
            DuckDuckGoSearchTool(), 
            VisitWebpageTool(),
            PythonInterpreterTool(),  # For code execution and data processing
            SpeechToTextTool(),  # For audio transcription
        ]
        
        # Initialize CodeAgent with default prompts (will enhance questions in run method)
        self.agent = CodeAgent(
            model=self.model, 
            tools=self.tools
        )
        # Store API URL for file downloads
        self.api_url = DEFAULT_API_URL
    
    def __call__(self, question: str) -> str:
        """
        Make the agent callable. This method handles file downloads internally
        by parsing the question for file references or task context.
        
        Args:
            question: The question to answer (may contain file references)
        """
        return self.run(question)
    
    def run(self, question: str) -> str:
        """
        Run the agent on a question. Automatically detects question type and enhances
        with appropriate instructions for the agent.
        
        Args:
            question: The question to answer
        """
        # Enhance question with instructions based on content analysis
        enhanced_question = question
        question_lower = question.lower()
        
        # Check for reversed text (starts with period, ends with capital letter)
        if question.strip().startswith('.') and len(question) > 20:
            enhanced_question = f"""{question}

NOTE: This text appears to be reversed. Please reverse it first using Python:
reversed_text = question[::-1] or ''.join(reversed(question))
Then answer based on the reversed text."""
        
        # Check for YouTube URLs
        elif 'youtube.com' in question or 'youtu.be' in question:
            enhanced_question = f"""{question}

NOTE: This question involves a YouTube video. Use VisitWebpageTool to access the video page,
or use DuckDuckGoSearchTool to search for information about this video, transcripts, or descriptions."""
        
        # Check for image/chess questions
        elif 'image' in question_lower or 'chess' in question_lower or 'position' in question_lower:
            enhanced_question = f"""{question}

NOTE: This question involves an image file (possibly a chess position). 
If you can access the file, load it with: from PIL import Image; img = Image.open(file_path)
For chess positions, identify all pieces (K=King, Q=Queen, R=Rook, B=Bishop, N=Knight, P=Pawn) 
and determine the best move in algebraic notation (e.g., "e4", "Nf3").
If the file is not available, try to use web search to find related information."""
        
        # Check for audio questions
        elif 'audio' in question_lower or 'mp3' in question_lower or 'recording' in question_lower or 'voice memo' in question_lower or 'listen' in question_lower:
            enhanced_question = f"""{question}

NOTE: This question involves an audio file. Use SpeechToTextTool to transcribe if the file is available.
Listen carefully for specific details like ingredients, page numbers, names, etc.
Extract only the requested information (e.g., just ingredients, not measurements).
If the file is not available, try to use web search to find related information."""
        
        # Check for Python code questions
        elif 'python code' in question_lower or ('code' in question_lower and 'python' in question_lower) or 'numeric output' in question_lower:
            enhanced_question = f"""{question}

NOTE: This question involves a Python code file. If you can access the file, read and execute it:
with open(file_path, 'r') as f: code = f.read()
Then execute the code and provide the final output or result.
If the file is not available, try to analyze the question logically."""
        
        # Check for Excel/spreadsheet questions
        elif 'excel' in question_lower or 'xlsx' in question_lower or 'spreadsheet' in question_lower or ('sales' in question_lower and 'file' in question_lower):
            enhanced_question = f"""{question}

NOTE: This question involves an Excel/spreadsheet file. If you can access the file, read it with pandas:
df = pd.read_excel(file_path) or pd.read_csv(file_path)
Filter data carefully (e.g., food vs drinks, specific categories) and perform calculations accurately.
Format answers as requested (e.g., USD with 2 decimals).
If the file is not available, try to use web search to find related data or information."""
        
        # Check for mathematical/logic problems
        elif ('table' in question_lower and ('operation' in question_lower or '*' in question)) or 'commutative' in question_lower:
            enhanced_question = f"""{question}

NOTE: This is a mathematical/logic problem. Use Python to compute step by step.
For operation tables, check all pairs systematically.
Format answers as requested (comma-separated, alphabetical order, etc.)."""
        
        # Check for Wikipedia/research questions
        elif 'wikipedia' in question_lower or 'nominated' in question_lower or 'paper' in question_lower or 'article' in question_lower:
            enhanced_question = f"""{question}

NOTE: This is a research question. Use DuckDuckGoSearchTool to find information.
For Wikipedia questions, search specifically on Wikipedia.
For multi-step questions, break them down and search iteratively.
Verify information from multiple sources when possible."""
        
        # Run the agent with enhanced question
        return self.agent.run(enhanced_question)

def get_hf_username():
    """Get Hugging Face username from CLI"""
    try:
        from huggingface_hub import whoami
        user_info = whoami()
        return user_info.get('name', None)
    except Exception as e:
        print(f"Error getting HF username: {e}")
        print("Make sure you're logged in with: huggingface-cli login")
        return None

def load_cached_answers():
    """Load cached answers from file if it exists"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cached_answers(cache_data):
    """Save answers to cache file"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

def process_questions(submit_after=False):
    """
    Run the agent on all questions and cache the answers.
    
    Args:
        submit_after: If True, submit answers after processing
    """
    username = get_hf_username()
    if not username:
        print("❌ Could not get Hugging Face username. Please login with: huggingface-cli login")
        return False
    
    print(f"✅ Logged in as: {username}")
    
    space_id = os.getenv("SPACE_ID", "your-space-id")
    api_url = DEFAULT_API_URL
    questions_url = f"{api_url}/questions"
    
    # 1. Instantiate Agent
    print("\n" + "="*60)
    print("Initializing Agent...")
    print("="*60)
    try:
        agent = BasicAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Error instantiating agent: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. Fetch Questions
    print(f"\nFetching questions from: {questions_url}")
    try:
        response = requests.get(questions_url, timeout=15)
        response.raise_for_status()
        questions_data = response.json()
        if not questions_data:
            print("❌ Fetched questions list is empty.")
            return False
        print(f"✅ Fetched {len(questions_data)} questions.")
    except Exception as e:
        print(f"❌ Error fetching questions: {e}")
        return False
    
    # 3. Load cached answers
    cache = load_cached_answers()
    answers_dict = cache.get('answers', {})
    cached_count = len(answers_dict)
    if cached_count > 0:
        print(f"📦 Found {cached_count} cached answers. Will skip those questions.")
    
    # 4. Run Agent on Questions
    results_log = []
    total_questions = len(questions_data)
    
    print(f"\n{'='*60}")
    print(f"Processing {total_questions} questions...")
    print(f"{'='*60}\n")
    
    for idx, item in enumerate(questions_data, 1):
        task_id = item.get("task_id")
        question_text = item.get("question")
        if not task_id or question_text is None:
            continue
        
        # Skip if already cached
        if task_id in answers_dict:
            print(f"⏭️  [{idx}/{total_questions}] Skipping (cached): {task_id}")
            results_log.append({
                "Task ID": task_id, 
                "Question": question_text[:80] + "..." if len(question_text) > 80 else question_text,
                "Status": "Cached"
            })
            continue
        
        print(f"\n{'='*60}")
        print(f"Question {idx}/{total_questions}")
        print(f"Task ID: {task_id}")
        print(f"Question: {question_text[:100]}..." if len(question_text) > 100 else f"Question: {question_text}")
        print(f"{'='*60}")
        
        try:
            result_container = {"answer": None, "error": None, "completed": False}
            
            def run_agent():
                try:
                    result_container["answer"] = agent(question_text)
                    result_container["completed"] = True
                except Exception as e:
                    result_container["error"] = e
                    result_container["completed"] = True
            
            print(f"⏳ Starting agent execution...")
            start_time = time.time()
            
            agent_thread = threading.Thread(target=run_agent, daemon=True)
            agent_thread.start()
            agent_thread.join(timeout=300)  # 5 minute timeout
            
            elapsed_time = time.time() - start_time
            
            if not result_container["completed"]:
                print(f"⏱️  TIMEOUT: Agent took too long (>5 minutes, elapsed: {elapsed_time:.2f}s)")
                error_msg = "TIMEOUT: Agent execution exceeded 5 minute limit"
                answers_dict[task_id] = error_msg
                results_log.append({"Task ID": task_id, "Status": "Timeout"})
            elif result_container["error"]:
                raise result_container["error"]
            else:
                submitted_answer = result_container["answer"]
                print(f"✅ Completed in {elapsed_time:.2f} seconds")
                print(f"Answer: {str(submitted_answer)[:200]}..." if len(str(submitted_answer)) > 200 else f"Answer: {submitted_answer}")
                
                answers_dict[task_id] = submitted_answer
                results_log.append({"Task ID": task_id, "Status": "Completed"})
                
        except Exception as e:
            print(f"❌ Error running agent on task {task_id}: {e}")
            import traceback
            traceback.print_exc()
            error_msg = f"AGENT ERROR: {str(e)[:200]}"
            answers_dict[task_id] = error_msg
            results_log.append({"Task ID": task_id, "Status": "Error"})
        
        # Save cache after each question
        cache['answers'] = answers_dict
        cache['username'] = username
        cache['timestamp'] = datetime.now().isoformat()
        save_cached_answers(cache)
        
        print(f"📊 Progress: {idx}/{total_questions} questions completed")
    
    # Summary
    print(f"\n{'='*60}")
    print("✅ Processing Complete!")
    print(f"{'='*60}")
    print(f"Total questions: {total_questions}")
    print(f"Answers generated: {len(answers_dict)}")
    print(f"Cached answers: {cached_count}")
    print(f"Cache saved to: {CACHE_FILE}")
    
    if submit_after:
        return submit_answers()
    else:
        print(f"\n💡 To submit answers, run: python app.py --submit")
        return True

def submit_answers():
    """Submit previously cached answers"""
    username = get_hf_username()
    if not username:
        print("❌ Could not get Hugging Face username. Please login with: huggingface-cli login")
        return False
    
    cache = load_cached_answers()
    if not cache.get('answers'):
        print("❌ No cached answers found. Please run: python app.py --process")
        return False
    
    answers_dict = cache['answers']
    space_id = os.getenv("SPACE_ID", "your-space-id")
    agent_code = f"https://huggingface.co/spaces/{space_id}/tree/main"
    api_url = DEFAULT_API_URL
    submit_url = f"{api_url}/submit"
    
    answers_payload = [{"task_id": tid, "submitted_answer": ans} for tid, ans in answers_dict.items()]
    
    submission_data = {
        "username": username.strip(), 
        "agent_code": agent_code, 
        "answers": answers_payload
    }
    
    print(f"\n{'='*60}")
    print(f"Submitting {len(answers_payload)} answers...")
    print(f"{'='*60}")
    print(f"Submit URL: {submit_url}")
    print(f"Username: {username}")
    
    try:
        response = requests.post(submit_url, json=submission_data, timeout=60)
        response.raise_for_status()
        result_data = response.json()
        
        print(f"\n{'='*60}")
        print("✅ Submission Successful!")
        print(f"{'='*60}")
        print(f"User: {result_data.get('username')}")
        print(f"Overall Score: {result_data.get('score', 'N/A')}%")
        print(f"Correct: {result_data.get('correct_count', '?')}/{result_data.get('total_attempted', '?')}")
        print(f"Message: {result_data.get('message', 'No message received.')}")
        
        # Clear cache after successful submission
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            print(f"\n🗑️  Cache cleared after successful submission.")
        
        return True
    except Exception as e:
        print(f"\n❌ Submission Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='HuggingFace Agents Course - Unit 4 Final Assignment')
    parser.add_argument('--process', action='store_true', help='Process all questions and cache answers')
    parser.add_argument('--submit', action='store_true', help='Submit cached answers')
    parser.add_argument('--process-and-submit', action='store_true', help='Process questions and submit immediately')
    
    args = parser.parse_args()
    
    load_dotenv()
    
    if args.process_and_submit:
        success = process_questions(submit_after=True)
        sys.exit(0 if success else 1)
    elif args.process:
        success = process_questions(submit_after=False)
        sys.exit(0 if success else 1)
    elif args.submit:
        success = submit_answers()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        print("\n💡 Examples:")
        print("  python app.py --process              # Process questions and cache answers")
        print("  python app.py --submit               # Submit cached answers")
        print("  python app.py --process-and-submit   # Process and submit in one go")
        sys.exit(1)

if __name__ == "__main__":
    main()
