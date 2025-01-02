# Video Translation Service

A robust service for handling video translation jobs with real-time status updates. This system provides a scalable architecture for managing asynchronous video translation tasks with features like real-time status updates, efficient job processing, and comprehensive error handling.

## Table of Contents
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Server](#server)
  - [Client Library](#client-library)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Features

- **Real-time Status Updates**: WebSocket-based status notifications
- **Robust Error Handling**: Dead Letter Queue (DLQ) for failed jobs
- **Caching**: Redis-based caching for improved performance
- **Scalable**: Async operations throughout

## Architecture Overview

The system consists of the following key components:

1. **FastAPI Server**
   - Handles job creation and status updates
   - WebSocket endpoints for real-time communication
   - Prometheus metrics endpoint

2. **Client Library**
   - WebSocket-based status monitoring
   - Automatic retry mechanism
   - Connection health monitoring via heartbeat
   - Configurable timeouts and error handling

3. **Job Processing System**
   - Async job processing
   - Configurable processing times
   - Simulated error rates for testing
   - Status update notifications

4. **Data Management**
   - PostgreSQL for persistent storage
   - Redis for caching and DLQ
   - Connection pooling
   - Transaction management


## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/video-translation-service.git
cd video-translation-service
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
# Create PostgreSQL database
createdb translation_db

# Run migrations
alembic upgrade head
```

5. Start Redis:
```bash
# Using Docker
docker run -d -p 6379:6379 redis

# Or install and run locally
redis-server
```

## Usage

### Server

Start the server:
```bash
uvicorn app.main:app --reload --port 8000
```

The server exposes the following endpoints:
- `POST /translate` - Create new translation job
- `WS /ws/job/{job_id}` - WebSocket endpoint for status updates
- `GET /metrics` - Prometheus metrics

### Client Library

```python
from translation_client import TranslationClient

async with TranslationClient("http://localhost:8000") as client:
    # Start a translation job
    response = await client.start_translation(
        source_language="en",
        target_language="es",
        metadata={"video_url": "https://example.com/video.mp4"}
    )
    
    # Wait for completion
    result = await client.wait_for_completion(response["job_id"])
    print(f"Translation completed: {result}")
```

Client Configuration Options:
```python
TranslationClient(
    base_url="http://localhost:8000",
    max_retries=3,
    retry_delay=1.0,
    timeout=30.0,
    heartbeat_interval=5.0
)
```

## API Documentation

### REST Endpoints

#### POST /translate
Create a new translation job.

Request:
```json
{
    "source_language": "en",
    "target_language": "es",
    "metadata": {
        "video_url": "https://example.com/video.mp4"
    }
}
```

Response:
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "message": "Translation job started"
}
```

### WebSocket Events

Connect to: `ws://localhost:8000/ws/job/{job_id}`

Status Updates:
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "completed_at": "2024-01-01T12:00:00Z"
}
```

## Development

### Project Structure
```
├── app/
│   ├── core/
│   │   ├── connection_manager.py
│   │   ├── job_processor.py
│   │   ├── cache_manager.py
│   │   └── dlq_manager.py
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── models/
│   │   └── schemas.py
│   └── main.py
├── tests/
│   ├── test_system.py
│   └── test_db.py
└── client/
    └── translation_client.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_system.py

```
