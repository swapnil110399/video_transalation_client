import asyncio
import uvicorn
import threading
import time
from server.app import app
from client.client import VideoTranslationClient


async def run_client():
    print("Starting client...")
    async with VideoTranslationClient("http://localhost:8000") as client:
        try:
            # Start translation
            response = await client.start_translation("en", "es")
            job_id = response["job_id"]
            print(f"Started translation job: {job_id}")

            # Wait for completion
            result = await client.wait_for_completion(job_id)
            print(f"Final result: {result}")

        except Exception as e:
            print(f"Error occurred: {e}")


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)


async def main():
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True  # Thread will be killed when main program exits
    server_thread.start()

    # Wait a bit for server to start
    time.sleep(2)

    # Run client
    await run_client()


if __name__ == "__main__":
    asyncio.run(main())
