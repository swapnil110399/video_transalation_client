import asyncio
from client.client import VideoTranslationClient, TranslationError
import aiohttp
from fastapi import FastAPI

"""
    An example application demonstrating translation client usage.

    This script provides a FastAPI server with a translation demo endpoint
    and a main function showcasing proper client usage with error handling.
"""

app = FastAPI()


@app.get("/")
async def root():
    """
    Root endpoint providing basic server status.

    :returns: Dictionary containing server status message
    """
    return {"message": "Hello from the root path!"}


async def main():
    """
    Demonstrate translation client usage with proper error handling.

    This function shows the recommended pattern for using the VideoTranslationClient,
    including context management and comprehensive error handling.

    The demonstration:
        1. Initializes client with async context manager
        2. Starts a sample translation job
        3. Waits for completion with status monitoring
        4. Handles all potential error conditions

    :raises:
        TranslationError: When translation processing fails
        aiohttp.ClientError: On network communication errors
        TimeoutError: When operations exceed time limits
    """
    async with VideoTranslationClient("http://localhost:8000/") as client:
        try:
            # Start a new translation job
            response = await client.start_translation("en", "es")
            print(f"Started translation job: {response.get('job_id')}")

            # Wait for job completion and get final result
            result = await client.wait_for_completion(response["job_id"])
            print(f"Final status: {result}")

        except TranslationError as e:
            # Handle translation-specific errors
            print(f"Translation Error: {e}")
        except aiohttp.ClientError as e:
            # Handle network and HTTP errors
            print(f"Aiohttp Error: {e}")
        except TimeoutError as e:
            # Handle timeout conditions
            print(f"Timeout Error: {e}")


if __name__ == "__main__":
    # Run the async main function when script is executed directly
    asyncio.run(main())
