import asyncio
import asyncpg


async def test_connection():
    """
    Test connection to PostgreSQL database.

    Attempts to establish a connection to PostgreSQL using asyncpg and
    verify it by retrieving the database version. This serves as a basic
    connectivity test.

    Returns:
        bool: True if connection successful, False otherwise

    Example:
        success = await test_connection()
        if success:
            print("Database connection working")
    """
    try:
        # Connect to the database with specified credentials
        conn = await asyncpg.connect(
            user="postgres",
            password="postgres",
            database="translation_db",
            host="localhost",
        )

        # Verify connection by getting PostgreSQL version
        version = await conn.fetchval("SELECT version();")
        print(f"Successfully connected to PostgreSQL!")
        print(f"PostgreSQL version: {version}")

        # Clean up connection
        await conn.close()
        return True

    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False


if __name__ == "__main__":
    """
    Script entry point.

    Executes the database connection test in an async context and
    prints the results.
    """
    asyncio.run(test_connection())
