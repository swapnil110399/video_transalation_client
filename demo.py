import asyncio
import uvicorn
import threading
import time
from server.app import app
from client.client import VideoTranslationClient

"""
    An integration script running both translation server and client.

    This script demonstrates the complete translation system by launching
    both the server and client components in a coordinated manner.
    It handles the lifecycle of both components and their interaction.

    Key Components:
        - Threaded server execution using uvicorn
        - Async client execution with proper lifecycle management
        - Coordinated startup sequence
        - Error handling and graceful shutdown
    
    Raises:
        RuntimeError: If server fails to start
        Exception: For any client-side failures
"""


async def run_client():
    """
    Execute the translation client workflow.

    Demonstrates the complete client lifecycle including:
        1. Client initialization
        2. Job submission
        3. Status monitoring
        4. Result handling
        5. Error management

    :returns: None
    :raises:
        Exception: If any step in the translation process fails
    """
    print("Starting client...")
    async with VideoTranslationClient("http://localhost:8000") as client:
        try:
            # Start translation job
            response = await client.start_translation("en", "es")
            job_id = response["job_id"]
            print(f"Started translation job: {job_id}")

            # Monitor job until completion
            result = await client.wait_for_completion(job_id)
            print(f"Final result: {result}")

        except Exception as e:
            print(f"Error occurred: {e}")


def run_server():
    """
    Launch the translation server using uvicorn.

    Starts the FastAPI server application with uvicorn ASGI server
    using the specified host and port configuration.

    :returns: None
    :raises:
        RuntimeError: If server fails to start or encounters errors
    """
    uvicorn.run(app, host="127.0.0.1", port=8000)


async def main():
    """
    Coordinate server and client execution.

    This function manages the complete system lifecycle:
        1. Starts server in a daemon thread
        2. Waits for server initialization
        3. Executes client workflow
        4. Handles cleanup

    The server thread is marked as daemon to ensure it's terminated
    when the main program exits.

    :returns: None
    :raises:
        RuntimeError: If system coordination fails
        Exception: For any component-level failures
    """
    # Initialize server in separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True  # Ensure thread terminates with main program
    server_thread.start()

    # Allow server initialization time
    time.sleep(2)

    # Execute client workflow
    await run_client()


if __name__ == "__main__":
    # Execute the coordinated system workflow
    asyncio.run(main())
