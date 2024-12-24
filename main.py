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
        4. Shows job cancellation
        5. Handles all potential error conditions

    :raises:
        TranslationError: When translation processing fails
        aiohttp.ClientError: On network communication errors
        TimeoutError: When operations exceed time limits
    """
    async with VideoTranslationClient("http://localhost:8000/") as client:
        try:
            # Start a new translation job
            response = await client.start_translation("en", "es")
            job_id = response["job_id"]
            print(f"Started translation job: {job_id}")

            # Start another job that we'll cancel
            response2 = await client.start_translation("en", "fr")
            job_id2 = response2["job_id"]
            print(f"Started second translation job: {job_id2}")

            # Wait briefly then cancel the second job
            await asyncio.sleep(2)
            try:
                cancel_result = await client.cancel_translation(job_id2)
                print(f"Cancelled second job: {cancel_result}")
            except TranslationError as e:
                print(f"Failed to cancel job: {e}")

            # Wait for the first job to complete
            result = await client.wait_for_completion(job_id)
            print(f"First job final status: {result}")

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
