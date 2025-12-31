import os
import gradio as gr
import requests
import inspect
import pandas as pd
import tempfile
from pathlib import Path
# (Keep Constants as is)
# --- Constants ---
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

from smolagents import (
    CodeAgent, 
    OpenAIModel, 
    Tool, 
    DuckDuckGoSearchTool, 
    VisitWebpageTool,
    PythonInterpreterTool,
    SpeechToTextTool
)
from dotenv import load_dotenv

class BasicAgent:
    def __init__(self):
        # Use gpt-4o for better performance on complex tasks
        self.model = OpenAIModel(model="gpt-4o")
        # Add more tools for better task handling
        self.tools = [
            DuckDuckGoSearchTool(), 
            VisitWebpageTool(),
            PythonInterpreterTool(),  # For code execution and data processing
            SpeechToTextTool(),  # For audio transcription
        ]
        # Add system message to guide the agent
        system_message = """You are a helpful AI agent that can answer questions using various tools.

IMPORTANT INSTRUCTIONS FOR DIFFERENT TASK TYPES:

1. REVERSED TEXT: If text appears backwards, reverse it using Python: text[::-1] or ''.join(reversed(text))

2. IMAGES: 
   - Load with: from PIL import Image; img = Image.open(file_path)
   - For chess positions: Identify all pieces (K=King, Q=Queen, R=Rook, B=Bishop, N=Knight, P=Pawn)
   - Analyze board state carefully and determine the best move in algebraic notation (e.g., "e4", "Nf3")

3. AUDIO FILES:
   - Use SpeechToTextTool to transcribe audio
   - Listen carefully for specific details like ingredients, page numbers, names, etc.
   - Extract only the requested information (e.g., just ingredients, not measurements)

4. PYTHON CODE:
   - Read the file: with open(file_path, 'r') as f: code = f.read()
   - Execute it safely and capture the final output
   - Return only the final numeric or string result

5. EXCEL/CSV FILES:
   - Read with pandas: df = pd.read_excel(file_path) or pd.read_csv(file_path)
   - Filter data carefully (e.g., food vs drinks, specific categories)
   - Perform calculations accurately
   - Format answers as requested (e.g., USD with 2 decimals)

6. WEB SEARCHES:
   - Use DuckDuckGoSearchTool for information retrieval
   - For Wikipedia questions, search specifically on Wikipedia
   - For multi-step questions, break them down and search iteratively
   - Verify information from multiple sources when possible

7. YOUTUBE VIDEOS:
   - Use VisitWebpageTool to access the video page
   - Search for video transcripts, descriptions, or related information
   - Use DuckDuckGoSearchTool with the video title/URL to find details
   - Look for closed captions or transcript information

8. MATHEMATICAL/LOGIC PROBLEMS:
   - Use Python to compute step by step
   - For operation tables, check all pairs systematically
   - Format answers as requested (comma-separated, alphabetical order, etc.)

9. COMPLEX REASONING:
   - Break down multi-step questions
   - Use web search to find intermediate information
   - Verify each step before proceeding

ANSWER FORMATTING:
- Follow exact format requirements (comma-separated, alphabetical, first name only, etc.)
- Provide only the requested information, nothing extra
- Be precise and accurate
- If uncertain, use tools to verify your answer

IMPORTANT: If a question mentions a file attachment but the file is not available:
- For image questions: Try to use web search to find similar information or descriptions
- For audio questions: If transcription is not possible, use web search to find related information
- For code questions: If code cannot be executed, try to analyze the question logically
- For data file questions: Use web search to find similar datasets or information
- Always provide your best answer based on available information and tools"""
        
        self.agent = CodeAgent(
            model=self.model, 
            tools=self.tools,
            system_message=system_message
        )
    
    def run(self, question: str, file_path: str = None) -> str:
        """
        Run the agent on a question, optionally with a file attachment.
        
        Args:
            question: The question to answer
            file_path: Optional path to a file attachment (image, audio, code, excel, etc.)
        """
        if file_path and os.path.exists(file_path):
            # Include file information in the question with clear instructions
            file_ext = Path(file_path).suffix.lower()
            file_name = Path(file_path).name
            
            if file_ext in ['.png', '.jpg', '.jpeg', '.gif']:
                question = f"""{question}

IMPORTANT: An image file is available at: {file_path}
File name: {file_name}
Please load this image using PIL/Pillow and analyze it carefully to answer the question.
For chess positions, identify all pieces and their positions, then determine the best move."""
            elif file_ext in ['.mp3', '.wav', '.m4a', '.ogg']:
                question = f"""{question}

IMPORTANT: An audio file is available at: {file_path}
File name: {file_name}
Please transcribe this audio file using SpeechToTextTool or appropriate audio processing libraries, then answer the question based on the transcription."""
            elif file_ext in ['.py']:
                question = f"""{question}

IMPORTANT: A Python code file is available at: {file_path}
File name: {file_name}
Please read this Python file, execute it, and provide the final output or result."""
            elif file_ext in ['.xlsx', '.xls']:
                question = f"""{question}

IMPORTANT: An Excel file is available at: {file_path}
File name: {file_name}
Please read this Excel file using pandas (pd.read_excel) and analyze the data to answer the question."""
            elif file_ext in ['.csv']:
                question = f"""{question}

IMPORTANT: A CSV file is available at: {file_path}
File name: {file_name}
Please read this CSV file using pandas (pd.read_csv) and analyze the data to answer the question."""
            else:
                question = f"""{question}

IMPORTANT: A file is available at: {file_path}
File name: {file_name}
Please read and analyze this file to answer the question."""
        
        return self.agent.run(question)

def run_and_submit_all( profile: gr.OAuthProfile | None):
    """
    Fetches all questions, runs the BasicAgent on them, submits all answers,
    and displays the results.
    """
    # --- Determine HF Space Runtime URL and Repo URL ---
    space_id = os.getenv("SPACE_ID") # Get the SPACE_ID for sending link to the code

    if profile:
        username= f"{profile.username}"
        print(f"User logged in: {username}")
    else:
        print("User not logged in.")
        return "Please Login to Hugging Face with the button.", None

    api_url = DEFAULT_API_URL
    questions_url = f"{api_url}/questions"
    submit_url = f"{api_url}/submit"

    # 1. Instantiate Agent ( modify this part to create your agent)
    try:
        agent = BasicAgent()
    except Exception as e:
        print(f"Error instantiating agent: {e}")
        return f"Error initializing agent: {e}", None
    # In the case of an app running as a hugging Face space, this link points toward your codebase ( usefull for others so please keep it public)
    agent_code = f"https://huggingface.co/spaces/{space_id}/tree/main"
    print(agent_code)

    # 2. Fetch Questions
    print(f"Fetching questions from: {questions_url}")
    try:
        response = requests.get(questions_url, timeout=15)
        response.raise_for_status()
        questions_data = response.json()
        if not questions_data:
             print("Fetched questions list is empty.")
             return "Fetched questions list is empty or invalid format.", None
        print(f"Fetched {len(questions_data)} questions.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching questions: {e}")
        return f"Error fetching questions: {e}", None
    except requests.exceptions.JSONDecodeError as e:
         print(f"Error decoding JSON response from questions endpoint: {e}")
         print(f"Response text: {response.text[:500]}")
         return f"Error decoding server response for questions: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred fetching questions: {e}")
        return f"An unexpected error occurred fetching questions: {e}", None

    # 3. Run your Agent
    results_log = []
    answers_payload = []
    print(f"Running agent on {len(questions_data)} questions...")
    for item in questions_data:
        task_id = item.get("task_id")
        question_text = item.get("question")
        file_name = item.get("file_name", "")
        if not task_id or question_text is None:
            print(f"Skipping item with missing task_id or question: {item}")
            continue
        
        # Download file if available
        file_path = None
        if file_name:
            try:
                file_url = f"{api_url}/files/{task_id}"
                print(f"Attempting to download file for task {task_id}: {file_name}")
                file_response = requests.get(file_url, timeout=30)
                if file_response.status_code == 200:
                    # Save file to temporary location
                    temp_dir = tempfile.mkdtemp()
                    file_path = os.path.join(temp_dir, file_name)
                    with open(file_path, 'wb') as f:
                        f.write(file_response.content)
                    print(f"✅ Downloaded file ({len(file_response.content)} bytes) to: {file_path}")
                elif file_response.status_code == 404:
                    print(f"⚠️  File not available via API for task {task_id} (404).")
                    print(f"   Note: Files may not be accessible through the API endpoint.")
                    print(f"   Agent will attempt to answer using question text and available tools.")
                else:
                    print(f"⚠️  Could not download file for task {task_id}: HTTP {file_response.status_code}")
                    print(f"   Agent will attempt to answer without the file.")
            except Exception as e:
                print(f"⚠️  Error downloading file for task {task_id}: {e}")
                print(f"   Agent will attempt to answer without the file.")
        
        try:
            submitted_answer = agent.run(question_text, file_path=file_path)
            answers_payload.append({"task_id": task_id, "submitted_answer": submitted_answer})
            results_log.append({"Task ID": task_id, "Question": question_text, "Submitted Answer": submitted_answer})
        except Exception as e:
             print(f"Error running agent on task {task_id}: {e}")
             results_log.append({"Task ID": task_id, "Question": question_text, "Submitted Answer": f"AGENT ERROR: {e}"})
        finally:
            # Clean up temporary file
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    os.rmdir(os.path.dirname(file_path))
                except:
                    pass

    if not answers_payload:
        print("Agent did not produce any answers to submit.")
        return "Agent did not produce any answers to submit.", pd.DataFrame(results_log)

    # 4. Prepare Submission 
    submission_data = {"username": username.strip(), "agent_code": agent_code, "answers": answers_payload}
    status_update = f"Agent finished. Submitting {len(answers_payload)} answers for user '{username}'..."
    print(status_update)

    # 5. Submit
    print(f"Submitting {len(answers_payload)} answers to: {submit_url}")
    try:
        response = requests.post(submit_url, json=submission_data, timeout=60)
        response.raise_for_status()
        result_data = response.json()
        final_status = (
            f"Submission Successful!\n"
            f"User: {result_data.get('username')}\n"
            f"Overall Score: {result_data.get('score', 'N/A')}% "
            f"({result_data.get('correct_count', '?')}/{result_data.get('total_attempted', '?')} correct)\n"
            f"Message: {result_data.get('message', 'No message received.')}"
        )
        print("Submission successful.")
        results_df = pd.DataFrame(results_log)
        return final_status, results_df
    except requests.exceptions.HTTPError as e:
        error_detail = f"Server responded with status {e.response.status_code}."
        try:
            error_json = e.response.json()
            error_detail += f" Detail: {error_json.get('detail', e.response.text)}"
        except requests.exceptions.JSONDecodeError:
            error_detail += f" Response: {e.response.text[:500]}"
        status_message = f"Submission Failed: {error_detail}"
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except requests.exceptions.Timeout:
        status_message = "Submission Failed: The request timed out."
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except requests.exceptions.RequestException as e:
        status_message = f"Submission Failed: Network error - {e}"
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except Exception as e:
        status_message = f"An unexpected error occurred during submission: {e}"
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df


# --- Build Gradio Interface using Blocks ---
with gr.Blocks() as demo:
    gr.Markdown("# Basic Agent Evaluation Runner")
    gr.Markdown(
        """
        **Instructions:**

        1.  Please clone this space, then modify the code to define your agent's logic, the tools, the necessary packages, etc ...
        2.  Log in to your Hugging Face account using the button below. This uses your HF username for submission.
        3.  Click 'Run Evaluation & Submit All Answers' to fetch questions, run your agent, submit answers, and see the score.

        ---
        **Disclaimers:**
        Once clicking on the "submit button, it can take quite some time ( this is the time for the agent to go through all the questions).
        This space provides a basic setup and is intentionally sub-optimal to encourage you to develop your own, more robust solution. For instance for the delay process of the submit button, a solution could be to cache the answers and submit in a seperate action or even to answer the questions in async.
        """
    )

    gr.LoginButton()

    run_button = gr.Button("Run Evaluation & Submit All Answers")

    status_output = gr.Textbox(label="Run Status / Submission Result", lines=5, interactive=False)
    # Removed max_rows=10 from DataFrame constructor
    results_table = gr.DataFrame(label="Questions and Agent Answers", wrap=True)

    run_button.click(
        fn=run_and_submit_all,
        outputs=[status_output, results_table]
    )

    if __name__ == "__main__":
        print("\n" + "-"*30 + " App Starting " + "-"*30)
        load_dotenv()
        # Check for SPACE_HOST and SPACE_ID at startup for information
        space_host_startup = os.getenv("SPACE_HOST")
        space_id_startup = os.getenv("SPACE_ID") # Get SPACE_ID at startup

        if space_host_startup:
            print(f"✅ SPACE_HOST found: {space_host_startup}")
            print(f"   Runtime URL should be: https://{space_host_startup}.hf.space")
        else:
            print("ℹ️  SPACE_HOST environment variable not found (running locally?).")

        if space_id_startup: # Print repo URLs if SPACE_ID is found
            print(f"✅ SPACE_ID found: {space_id_startup}")
            print(f"   Repo URL: https://huggingface.co/spaces/{space_id_startup}")
            print(f"   Repo Tree URL: https://huggingface.co/spaces/{space_id_startup}/tree/main")
        else:
            print("ℹ️  SPACE_ID environment variable not found (running locally?). Repo URL cannot be determined.")

        print("-"*(60 + len(" App Starting ")) + "\n")

        print("Launching Gradio Interface for Basic Agent Evaluation...")
        demo.launch(debug=True, share=False)