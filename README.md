# Task Manager API

A simple REST API for managing tasks, built with **FastAPI**, **PostgreSQL**, and **Docker**. This project demonstrates modern Python backend development with async programming, database integration, and containerization.

## 🎯 Features

- ✅ **CRUD Operations**: Create, Read, Update, Delete tasks
- ✅ **Async Programming**: Built with FastAPI's async/await for high performance
- ✅ **PostgreSQL Database**: Persistent data storage with proper schema
- ✅ **Docker & Docker Compose**: Easy setup and deployment
- ✅ **Type Safety**: Pydantic models for request/response validation
- ✅ **Error Handling**: Proper HTTP status codes and error messages
- ✅ **API Documentation**: Auto-generated Swagger UI at `/docs`

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐
│  FastAPI    │─────────│  PostgreSQL  │
│  (Port 8001)│         │  (Port 5433) │
└─────────────┘         └──────────────┘
       ↓
   Docker Container
```

**Tech Stack:**
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 15 (Alpine)
- **ORM**: SQLAlchemy 2.0 with async support
- **Async Driver**: asyncpg
- **Server**: Uvicorn
- **Containerization**: Docker & Docker Compose

## 📋 Project Structure

```
.
├── main.py                 # FastAPI application & endpoints
├── models.py              # SQLAlchemy ORM models & Pydantic schemas
├── database.py            # Database connection & session management
├── requirements.txt       # Python dependencies
├── Dockerfile             # FastAPI container configuration
├── docker-compose.yml     # Multi-container setup
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git (optional, for version control)

### Installation & Running

1. **Clone the repository** (if you haven't already):
```bash
git clone https://github.com/YourUsername/Personal-Task-Manager-API.git
cd Personal-Task-Manager-API
```

2. **Start the services**:
```bash
docker compose up --build
```

You should see:
```
✅ Container task_manager_db   Running
✅ Container task_manager_app  Running
✅ Application startup complete
```

3. **Test the API**:
```bash
curl http://localhost:8001/
```

Expected response:
```json
{"message":"Task Manager API is running! 🚀"}
```

## 📡 API Endpoints

### Health Check
```bash
GET /
```
Returns: `{"message":"Task Manager API is running! 🚀"}`

### Create a Task
```bash
POST /tasks
Content-Type: application/json

{
  "title": "Learn Docker",
  "description": "Understand containers and Docker Compose",
  "status": "in_progress"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "title": "Learn Docker",
  "description": "Understand containers and Docker Compose",
  "status": "in_progress",
  "created_at": "2026-05-21T20:30:00+00:00"
}
```

### Get All Tasks
```bash
GET /tasks
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "title": "Learn Docker",
    "description": "Understand containers and Docker Compose",
    "status": "in_progress",
    "created_at": "2026-05-21T20:30:00+00:00"
  },
  {
    "id": 2,
    "title": "Learn FastAPI",
    "description": "Build REST APIs",
    "status": "pending",
    "created_at": "2026-05-21T20:35:00+00:00"
  }
]
```

### Get a Specific Task
```bash
GET /tasks/1
```

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Learn Docker",
  "description": "Understand containers and Docker Compose",
  "status": "in_progress",
  "created_at": "2026-05-21T20:30:00+00:00"
}
```

### Update a Task
```bash
PATCH /tasks/1
Content-Type: application/json

{
  "status": "completed"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Learn Docker",
  "description": "Understand containers and Docker Compose",
  "status": "completed",
  "created_at": "2026-05-21T20:30:00+00:00"
}
```

### Delete a Task
```bash
DELETE /tasks/1
```

**Response** (200 OK):
```json
{"message":"Task 1 deleted successfully"}
```

## 🔍 Interactive API Documentation

FastAPI auto-generates interactive API docs:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

You can test all endpoints directly from these interfaces!

## 🗄️ Database Schema

### Tasks Table
```sql
CREATE TABLE tasks (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description VARCHAR,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**Columns:**
- `id`: Auto-incrementing primary key
- `title`: Task title (required, max 255 chars)
- `description`: Detailed description (optional)
- `status`: One of `pending`, `in_progress`, `completed`
- `created_at`: Timestamp when task was created

## 💡 Key Concepts Explained

### Async/Await
All endpoints use `async def` to handle multiple requests simultaneously without blocking. This makes the API fast and efficient.

```python
@app.get("/tasks")
async def get_all_tasks(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(TaskDB))
    return result.scalars().all()
```

### Dependency Injection
`Depends(get_session)` automatically provides a database session to each endpoint:

```python
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    # session is automatically provided by FastAPI
    result = await session.execute(select(TaskDB).where(TaskDB.id == task_id))
```

### Pydantic Models
Request/response validation happens automatically:

```python
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
```

FastAPI validates the JSON and converts it to a Python object.

### SQLAlchemy ORM
Define tables as Python classes:

```python
class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    # ...
```

## 🛑 Error Handling

The API returns appropriate HTTP status codes:

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | GET, PATCH, DELETE worked |
| 201 | Created | POST created new task |
| 404 | Not Found | Task ID doesn't exist |
| 422 | Validation Error | Invalid request body |
| 500 | Server Error | Database connection failed |

## 🧪 Testing Examples

### Create 3 tasks:
```bash
curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Task 1","status":"pending"}'

curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Task 2","status":"in_progress"}'

curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Task 3","status":"completed"}'
```

### Get all tasks:
```bash
curl http://localhost:8001/tasks | jq
```

### Update task 2:
```bash
curl -X PATCH http://localhost:8001/tasks/2 \
  -H "Content-Type: application/json" \
  -d '{"status":"completed","title":"Updated Task 2"}'
```

### Delete task 3:
```bash
curl -X DELETE http://localhost:8001/tasks/3
```

## 📚 Learning Resources

This project teaches:
- **Docker**: Containerization and Docker Compose
- **FastAPI**: Building modern REST APIs in Python
- **PostgreSQL**: Relational databases and SQL
- **SQLAlchemy**: Python ORM for database operations
- **Async Programming**: asyncio and async/await
- **API Design**: RESTful principles, status codes, error handling

## 🔧 Environment Variables

Create a `.env` file based on `.env.example`:

```
DATABASE_URL=postgresql+asyncpg://taskuser:taskpass@db:5432/taskdb
ENVIRONMENT=development
```

## 🐛 Troubleshooting

### Port already in use
If port 8001 or 5433 is already in use, modify `docker-compose.yml`:
```yaml
ports:
  - "8002:8000"  # Change 8002 to another port
```

### Docker not running
Make sure Docker Desktop (or OrbStack on Mac) is running.

### Database connection errors
Check Docker logs:
```bash
docker compose logs db
docker compose logs web
```

### Container won't start
Rebuild the image:
```bash
docker compose down
docker compose up --build
```

## 📈 Future Enhancements

- [ ] Add user authentication (JWT tokens)
- [ ] Add task filtering and sorting
- [ ] Add pagination for large task lists
- [ ] Add task categories/tags
- [ ] Add due dates and reminders
- [ ] Add unit tests
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Deploy to cloud (AWS, Heroku, Railway)

## 📝 License

This project is open source and available under the MIT License.

## 👤 Author

**Tejas Malhotra**
- Email: tejas.malhotra.14@gmail.com
- GitHub: [@YourUsername](https://github.com/YourUsername)

---

**Happy coding!** 🚀 If you found this helpful, please star the repository!
