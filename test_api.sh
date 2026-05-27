#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8001"

echo -e "${BLUE}🧪 Testing Task Manager API${NC}\n"

# Test 1: Health Check
echo -e "${BLUE}1️⃣  Testing Health Check (GET /)${NC}"
curl -s $BASE_URL/ | jq .
echo -e "\n"

# Test 2: Create Task 1
echo -e "${BLUE}2️⃣  Creating Task 1 (POST /tasks)${NC}"
TASK1=$(curl -s -X POST $BASE_URL/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn Docker",
    "description": "Understand containers and Docker Compose",
    "status": "in_progress"
  }')
echo "$TASK1" | jq .
TASK1_ID=$(echo "$TASK1" | jq '.id')
echo -e "\n"

# Test 3: Create Task 2
echo -e "${BLUE}3️⃣  Creating Task 2 (POST /tasks)${NC}"
TASK2=$(curl -s -X POST $BASE_URL/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn FastAPI",
    "description": "Build REST APIs with Python",
    "status": "pending"
  }')
echo "$TASK2" | jq .
TASK2_ID=$(echo "$TASK2" | jq '.id')
echo -e "\n"

# Test 4: Create Task 3
echo -e "${BLUE}4️⃣  Creating Task 3 (POST /tasks)${NC}"
TASK3=$(curl -s -X POST $BASE_URL/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy to Production",
    "description": "Get the app running on a live server",
    "status": "pending"
  }')
echo "$TASK3" | jq .
TASK3_ID=$(echo "$TASK3" | jq '.id')
echo -e "\n"

# Test 5: Get All Tasks
echo -e "${BLUE}5️⃣  Getting All Tasks (GET /tasks)${NC}"
curl -s $BASE_URL/tasks | jq .
echo -e "\n"

# Test 6: Get Specific Task
echo -e "${BLUE}6️⃣  Getting Task $TASK1_ID (GET /tasks/$TASK1_ID)${NC}"
curl -s $BASE_URL/tasks/$TASK1_ID | jq .
echo -e "\n"

# Test 7: Update Task
echo -e "${BLUE}7️⃣  Updating Task $TASK1_ID to completed (PATCH /tasks/$TASK1_ID)${NC}"
curl -s -X PATCH $BASE_URL/tasks/$TASK1_ID \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }' | jq .
echo -e "\n"

# Test 8: Delete Task
echo -e "${BLUE}8️⃣  Deleting Task $TASK3_ID (DELETE /tasks/$TASK3_ID)${NC}"
curl -s -X DELETE $BASE_URL/tasks/$TASK3_ID | jq .
echo -e "\n"

# Test 9: Verify Deletion
echo -e "${BLUE}9️⃣  Verifying All Remaining Tasks (GET /tasks)${NC}"
curl -s $BASE_URL/tasks | jq .
echo -e "\n"

echo -e "${GREEN}✅ All tests completed!${NC}"
echo -e "${GREEN}📊 Summary:${NC}"
echo -e "  - Created 3 tasks"
echo -e "  - Updated 1 task (changed status to completed)"
echo -e "  - Deleted 1 task"
echo -e "  - Now have 2 remaining tasks in the database"
