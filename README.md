# Video Translation Service

A robust asynchronous video translation service implementation featuring a FastAPI server and an intelligent client with advanced polling mechanisms.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Components](#components)
  - [Server](#server)
  - [Client](#client)
  - [Integration](#integration)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Error Handling](#error-handling)
- [Configuration](#configuration)

## Overview

This project implements a scalable video translation service with asynchronous processing capabilities. It consists of a FastAPI-based server for handling translation jobs and a sophisticated client library that manages job submission and status monitoring.

## Features

- Asynchronous job processing
- Intelligent polling with progressive delay
- Comprehensive error handling
- Thread-safe job management
- Configurable timeout and retry mechanisms
- Detailed logging system
- Integration testing support

## System Architecture

The system is composed of two main components:

1. **Translation Server**: A FastAPI application managing translation jobs
2. **Client Library**: An async client with intelligent polling mechanisms

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/video-translation-service.git

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

The application consists of multiple components that need to be started in the correct order:

1. First, start the server:
```python
# Start the FastAPI server independently
uvicorn server:app --host 0.0.0.0 --port 8000
```

2. Then you can either run the demo (which includes both server and client) or the main application:
```python
# Run the demo (includes both server and client)
python demo.py

# OR run the main application
python main.py
```

Note: If you run `demo.py`, it will start its own server instance, so make sure you're not running the server separately in this case.

2. Use the client:
```python
import asyncio
from client import VideoTranslationClient

async def main():
    async with VideoTranslationClient("http://localhost:8000") as client:
        # Start translation
        response = await client.start_translation("en", "es")
        job_id = response["job_id"]
        
        # Wait for completion
        result = await client.wait_for_completion(job_id)
        print(f"Translation completed: {result}")

asyncio.run(main())
```

## Running Modes

The application supports different running modes:

1. **Standalone Server** (`app.py`):
   - Runs only the FastAPI server
   - Best for development and when you want to run client separately
   - Use this when you want to test with custom clients

2. **Demo Mode** (`demo.py`):
   - Runs both server and client in a coordinated manner
   - Includes a complete integration example
   - Useful for testing and demonstration purposes

3. **Main Application** (`main.py`):
   - Runs a FastAPI server with a translation demo endpoint
   - Includes example client usage
   - Best for production deployment

Choose the appropriate mode based on your needs. Remember that you should not run multiple servers on the same port (8000 by default).

## Components

### Server (app.py)

The server component provides a robust translation job processing system with the following key features:

- Thread-safe job storage
- Configurable processing times
- Simulated error rates for testing
- Comprehensive logging

#### Key Classes:

1. **TranslationJob**
```python
class TranslationJob(BaseModel):
    job_id: str
    status: str
    source_language: str
    target_language: str
    created_at: datetime
    error_message: Optional[str] = None
```

2. **TranslationServer**
```python
class TranslationServer:
    def __init__(self, error_rate=0.05):
        self.jobs = {}
        self.error_rate = error_rate
        self._lock = threading.Lock()
```

### Client (client.py)

The client library provides a sophisticated interface for interacting with the translation service:

#### Key Classes:

1. **TranslationConfig**
```python
class TranslationConfig:
    def __init__(
        self,
        base_timeout=30,
        min_delay=0.5,
        max_delay=3.0,
        progressive_delay=True
    ):
        self.base_timeout = base_timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.progressive_delay = progressive_delay
```

2. **VideoTranslationClient**
```python
class VideoTranslationClient:
    async def start_translation(
        self,
        source_lang: str,
        target_lang: str
    ) -> Dict[str, Any]:
        # Start a new translation job
        pass

    async def wait_for_completion(self, job_id: str) -> Dict[str, Any]:
        # Wait for job completion with intelligent polling
        pass
```

## API Documentation

### Server Endpoints

1. **Start Translation**
```
POST /translate
```
Request Body:
```json
{
    "job_id": "string",
    "source_language": "string",
    "target_language": "string"
}
```
Response:
```json
{
    "message": "Translation started",
    "job_id": "string"
}
```

2. **Get Job Status**
```
GET /job/{job_id}
```
Response:
```json
{
    "job_id": "string",
    "status": "string",
    "source_language": "string",
    "target_language": "string",
    "created_at": "datetime",
    "error_message": "string"
}
```

### Client API

1. **Initialize Client**
```python
client = VideoTranslationClient(
    base_url="http://localhost:8000",
    config=TranslationConfig(
        base_timeout=30,
        min_delay=0.5,
        max_delay=3.0,
        progressive_delay=True
    )
)
```

2. **Start Translation**
```python
response = await client.start_translation("en", "es")
job_id = response["job_id"]
```

3. **Monitor Job**
```python
result = await client.wait_for_completion(job_id)
```

## Testing

The project includes integration tests using pytest:

```python
pytest test_integration.py
```

Key test features:
- Automated server startup
- Client workflow testing
- Error condition validation
- Async test support

## Error Handling

The system implements comprehensive error handling:

1. **Client Errors**
- TranslationError: Custom exception for translation failures
- TimeoutError: When jobs exceed configured timeout
- aiohttp.ClientError: For network-related issues

2. **Server Errors**
- HTTPException: For API-level errors
- RuntimeError: For internal server issues

## Configuration

### Server Configuration
- Error rate simulation: Configurable probability of random errors
- Processing time simulation: Random delays between 5-15 seconds

### Client Configuration
- Base timeout: Maximum wait time for job completion
- Min/Max delay: Bounds for polling intervals
- Progressive delay: Enable/disable adaptive polling
