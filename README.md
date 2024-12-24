# Video Translation Client Library

## Overview
A robust, production-ready client library for interacting with video translation services, designed with developer experience and reliability in mind. This library provides an intuitive interface for managing video translation jobs with smart polling, error handling, and configurable behavior.

## 🌟 Key Features

### Smart Polling with Progressive Delays
- Implements an intelligent polling strategy that automatically adjusts request frequency
- Starts with quick checks and progressively increases intervals to reduce server load
- Resets to quick polling when status changes are detected
- Configurable minimum and maximum delays

### Robust Error Handling
- Custom `TranslationError` class for clear error identification
- Comprehensive timeout handling
- Detailed error messages and logging
- HTTP error management and retry logic

### Async/Await Support
- Built on modern async/await patterns
- Efficient handling of concurrent requests
- Non-blocking operations for better performance

### Comprehensive Logging
- Detailed logging at multiple levels (INFO, DEBUG, ERROR)
- Transaction tracing through unique job IDs
- Performance monitoring capabilities

## 🚀 Quick Start

### Installation
```bash
pip install video-translation-client

# Required dependencies
pip install aiohttp fastapi uvicorn
```

### Basic Usage
```python
import asyncio
from video_translation_client import VideoTranslationClient

async def translate_video():
    async with VideoTranslationClient("http://api.example.com") as client:
        # Start translation
        response = await client.start_translation("en", "es")
        job_id = response["job_id"]
        
        # Wait for completion
        result = await client.wait_for_completion(job_id)
        print(f"Translation completed: {result}")

# Run the async function
asyncio.run(translate_video())
```

## ⚙️ Configuration Options

### TranslationConfig
Customize the client behavior using the `TranslationConfig` class:

```python
from video_translation_client import TranslationConfig, VideoTranslationClient

config = TranslationConfig(
    base_timeout=30,      # Maximum time to wait for job completion
    min_delay=0.5,        # Minimum delay between status checks
    max_delay=3.0,        # Maximum delay between status checks
    progressive_delay=True # Enable/disable progressive delay
)

client = VideoTranslationClient("http://api.example.com", config)
```

## 🔍 Detailed Feature Documentation

### Progressive Polling Strategy
The library implements a smart polling strategy that:
1. Starts with frequent checks (min_delay)
2. Gradually increases delay if status remains unchanged
3. Resets to quick polling when status changes
4. Caps at max_delay to ensure responsiveness

```python
# Example configuration for different scenarios
# Quick updates priority
config_quick = TranslationConfig(min_delay=0.2, max_delay=1.0)

# Server-friendly configuration
config_efficient = TranslationConfig(min_delay=1.0, max_delay=5.0)
```

### Error Handling
The library provides comprehensive error handling:

```python
try:
    result = await client.wait_for_completion(job_id)
except TranslationError as e:
    print(f"Translation failed: {e}")
except TimeoutError as e:
    print(f"Operation timed out: {e}")
except aiohttp.ClientError as e:
    print(f"Network error: {e}")
```

### Logging Integration
Built-in logging with customizable levels:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video_translation_client")
```

## 🔧 Advanced Usage

### Custom Session Management
```python
async with aiohttp.ClientSession() as session:
    client = VideoTranslationClient("http://api.example.com", session=session)
    # Use client with custom session
```

### Status Monitoring
```python
async def monitor_translation(client, job_id):
    while True:
        status = await client.get_status(job_id)
        if status["status"] in ["completed", "error"]:
            break
        print(f"Current status: {status}")
        await asyncio.sleep(1)
```

## 🧪 Testing

The library comes with comprehensive integration tests:

```bash
# Run the test suite
pytest test_integration.py -v
```

Example test:
```python
@pytest.mark.asyncio
async def test_translation_flow():
    async with VideoTranslationClient("http://localhost:8000") as client:
        response = await client.start_translation("en", "es")
        result = await client.wait_for_completion(response["job_id"])
        assert result["status"] == "completed"
```

## 📊 Performance Considerations

### Resource Management
- Uses connection pooling for efficient HTTP connections
- Implements proper resource cleanup with context managers
- Configurable timeouts to prevent resource leaks

### Server Load
The progressive delay strategy helps manage server load by:
- Reducing unnecessary polling
- Adapting to server response patterns
- Providing configurable limits

## 🤝 Contributing

We welcome contributions! Please see our contributing guide for details.

1. Fork the repository
2. Create your feature branch
3. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Projects

- [Video Translation Server](link-to-server)
- [Video Translation CLI](link-to-cli)
- [Video Translation Dashboard](link-to-dashboard)

## 🎯 Design Philosophy

This library was built with the following principles in mind:

1. **Developer Experience First**
   - Intuitive API design
   - Comprehensive documentation
   - Clear error messages

2. **Production Readiness**
   - Robust error handling
   - Performance optimization
   - Resource management

3. **Flexibility**
   - Configurable behavior
   - Extensible design
   - Modern async support

4. **Reliability**
   - Smart retry logic
   - Timeout handling
   - Comprehensive logging

## 🤔 FAQs

**Q: Why use progressive delays?**
A: Progressive delays help balance responsiveness with server load. It starts with quick checks for active jobs while preventing unnecessary load during longer operations.

**Q: How does error handling work?**
A: The library provides custom exceptions and detailed error messages. It handles network errors, timeouts, and service-specific errors with appropriate retry logic.

**Q: Can I customize the polling behavior?**
A: Yes, through the `TranslationConfig` class you can adjust minimum and maximum delays, timeout duration, and enable/disable progressive delay.

## 📞 Support

For support, please:
1. Check the documentation
2. Look through existing issues
3. Create a new issue if needed
4. Contact support@example.com

## 🔄 Version History

- 1.0.0: Initial release
- 1.1.0: Added progressive delay feature
- 1.2.0: Enhanced error handling
- 1.3.0: Improved logging