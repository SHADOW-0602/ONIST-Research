import asyncio
import logging
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.pipeline.notebook_client import notebook_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing CockroachDB schema for ONIST-Research...")
    try:
        await notebook_client.initialize_schema()
        logger.info("Schema initialization successful.")
    except Exception as e:
        logger.error(f"Schema initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
