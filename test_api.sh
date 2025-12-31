#!/bin/bash
# Simple API test script using curl

echo "=========================================="
echo "Testing Agent Evaluation API"
echo "=========================================="
echo ""

echo "1. Testing /questions endpoint..."
curl -s "https://agents-course-unit4-scoring.hf.space/questions" | python3 -m json.tool | head -30
echo ""
echo ""

echo "2. Testing /random-question endpoint..."
curl -s "https://agents-course-unit4-scoring.hf.space/random-question" | python3 -m json.tool
echo ""
echo ""

echo "3. Testing file download (using a sample task_id from questions)..."
# First get a question with a file
TASK_ID=$(curl -s "https://agents-course-unit4-scoring.hf.space/questions" | python3 -c "import sys, json; data=json.load(sys.stdin); files=[q for q in data if q.get('file_name')]; print(files[0]['task_id'] if files else '')" 2>/dev/null)
if [ ! -z "$TASK_ID" ]; then
    echo "Testing file download for task_id: $TASK_ID"
    curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "https://agents-course-unit4-scoring.hf.space/files/$TASK_ID"
else
    echo "No files found in questions to test"
fi
echo ""

echo "=========================================="
echo "API Testing Complete"
echo "=========================================="
