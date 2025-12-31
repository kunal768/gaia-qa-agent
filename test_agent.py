"""
Test script to verify agent performance on individual questions
"""
import os
import requests
import tempfile
from pathlib import Path
from app import BasicAgent
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

def test_fetch_questions():
    """Test fetching all questions"""
    print("=" * 60)
    print("Testing: Fetch All Questions")
    print("=" * 60)
    try:
        response = requests.get(f"{DEFAULT_API_URL}/questions", timeout=15)
        response.raise_for_status()
        questions = response.json()
        print(f"✅ Successfully fetched {len(questions)} questions")
        if questions:
            print(f"\nSample question:")
            print(f"  Task ID: {questions[0].get('task_id')}")
            print(f"  Question: {questions[0].get('question')[:100]}...")
            print(f"  File: {questions[0].get('file_name', 'None')}")
        return questions
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_fetch_random_question():
    """Test fetching a random question"""
    print("\n" + "=" * 60)
    print("Testing: Fetch Random Question")
    print("=" * 60)
    try:
        response = requests.get(f"{DEFAULT_API_URL}/random-question", timeout=15)
        response.raise_for_status()
        question = response.json()
        print(f"✅ Successfully fetched random question")
        print(f"  Task ID: {question.get('task_id')}")
        print(f"  Question: {question.get('question')[:200]}...")
        print(f"  File: {question.get('file_name', 'None')}")
        return question
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_fetch_file(task_id, file_name):
    """Test fetching a file for a task"""
    if not file_name:
        return None
    print(f"\nTesting file download for task {task_id}...")
    try:
        response = requests.get(f"{DEFAULT_API_URL}/files/{task_id}", timeout=30)
        if response.status_code == 200:
            print(f"✅ Successfully downloaded file: {file_name}")
            return response.content
        elif response.status_code == 404:
            print(f"ℹ️  No file available for task {task_id}")
            return None
        else:
            print(f"⚠️  HTTP {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return None

def test_agent_on_questions(num_questions=5):
    """Test the agent on a few questions"""
    print("\n" + "=" * 60)
    print(f"Testing Agent on {num_questions} Questions")
    print("=" * 60)
    
    # Fetch questions
    questions = test_fetch_questions()
    if not questions:
        print("❌ Could not fetch questions")
        return
    
    # Initialize agent
    try:
        agent = BasicAgent()
        print("\n✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        return
    
    # Test on first few questions
    test_questions = questions[:num_questions]
    results = []
    
    for i, item in enumerate(test_questions, 1):
        task_id = item.get("task_id")
        question_text = item.get("question")
        file_name = item.get("file_name", "")
        
        print(f"\n--- Question {i}/{len(test_questions)} ---")
        print(f"Task ID: {task_id}")
        print(f"Question: {question_text[:150]}...")
        print(f"File: {file_name if file_name else 'None'}")
        
        # Download file if available
        file_path = None
        if file_name:
            file_content = test_fetch_file(task_id, file_name)
            if file_content:
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, file_name)
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                print(f"File saved to: {file_path}")
        
        # Run agent
        try:
            print("Running agent...")
            answer = agent.run(question_text, file_path=file_path)
            print(f"✅ Answer: {answer[:200]}...")
            results.append({
                "task_id": task_id,
                "question": question_text,
                "answer": answer,
                "success": True
            })
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "task_id": task_id,
                "question": question_text,
                "answer": f"ERROR: {e}",
                "success": False
            })
        finally:
            # Clean up
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    os.rmdir(os.path.dirname(file_path))
                except:
                    pass
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    successful = sum(1 for r in results if r["success"])
    print(f"Successfully answered: {successful}/{len(results)}")
    print(f"\nDetailed results:")
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"{status} {r['task_id']}: {r['answer'][:100]}...")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Agent Testing Script")
    print("=" * 60)
    
    # Test API endpoints
    test_fetch_questions()
    test_fetch_random_question()
    
    # Test agent on questions
    test_agent_on_questions(num_questions=5)
    
    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)
