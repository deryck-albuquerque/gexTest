import asyncio

from app.workers.distributor import start_sms_worker


if __name__ == "__main__":
    asyncio.run(start_sms_worker())