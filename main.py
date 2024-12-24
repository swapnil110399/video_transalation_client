import asyncio
from client.client import VideoTranslationClient, TranslationError
import aiohttp  # Make sure to install aiohttp: pip install aiohttp
from fastapi import FastAPI

app = FastAPI()


@app.get("/")  # Add this route handler
async def root():
    return {"message": "Hello from the root path!"}


async def main():
    async with VideoTranslationClient("http://0.0.0.0:8000/") as client:
        try:
            response = await client.start_translation("en", "es")
            print(f"Started translation job: {response.get('job_id')}")

            result = await client.wait_for_completion(response["job_id"])
            print(f"Final status: {result}")

        except TranslationError as e:  # Catch the new exception
            print(f"Translation Error: {e}")  # Print informative error message
        except aiohttp.ClientError as e:
            print(f"Aiohttp Error: {e}")
        except TimeoutError as e:
            print(f"Timeout Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
