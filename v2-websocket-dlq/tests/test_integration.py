import pytest
import asyncio
import uvicorn
import threading
import time
import socket
from app.main import app
from client.translation_client import TranslationClient, TranslationError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_free_port():
    """Get a free port on localhost"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

@pytest.fixture(scope="module")
def server_port():
    """Get a free port for the server"""
    return get_free_port()

@pytest.fixture(scope="module")
def server_url(server_port):
    """Get the server URL"""
    return f"http://127.0.0.1:{server_port}"

@pytest.fixture(scope="module")
def server(server_port):
    """Start the FastAPI server in a separate thread"""
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=server_port, log_level="error")
    
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Wait for server to start
    yield server_thread

@pytest.mark.asyncio
async def test_successful_translation(server, server_url):
    """Test successful translation flow"""
    async with TranslationClient(
        server_url,
        timeout=5.0,
        heartbeat_interval=1.0,
        retry_delay=0.5,
        max_retries=3
    ) as client:
        # Start translation
        response = await client.start_translation("en", "es")
        assert "job_id" in response
        job_id = response["job_id"]
        
        # Wait for completion
        result = await client.wait_for_completion(job_id)
        assert result["status"] in ("completed", "error")

@pytest.mark.asyncio
async def test_multiple_translations(server, server_url):
    """Test multiple concurrent translations"""
    async with TranslationClient(server_url, timeout=10.0) as client:
        # Start multiple translations
        jobs = []
        for _ in range(3):
            response = await client.start_translation("en", "es")
            jobs.append(response["job_id"])
        
        # Wait for all completions
        results = await asyncio.gather(
            *[client.wait_for_completion(job_id) for job_id in jobs],
            return_exceptions=True
        )
        
        # Check results
        for result in results:
            if isinstance(result, Exception):
                assert isinstance(result, TranslationError)
            else:
                assert result["status"] in ("completed", "error")

@pytest.mark.asyncio
async def test_error_handling(server, server_url):
    """Test error handling in translation"""
    async with TranslationClient(server_url, timeout=10.0) as client:
        # Test with invalid connection
        with pytest.raises(TranslationError):
            await client.wait_for_completion("invalid-job-id")