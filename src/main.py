import asyncio
import json
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WCP-Client")


class WcpMessageType(Enum):
    COMMAND = "command"
    RESPONSE = "response"
    EVENT = "event"
    GREETING = "greeting"
    ERROR = "error"

    @classmethod
    def from_str(cls, label: str):
        try:
            return cls(label.lower())
        except ValueError:
            return None


class WCPAsyncClient:
    def __init__(self, host="localhost", port=54321):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.is_connected = False

    async def connect(self):
        try:
            logger.info(f"Connecting to {self.host}:{self.port}")
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self.is_connected = True
            logger.info("Connected sucessfully")
        except Exception as e:
            self.is_connected = False
            logger.error(f"Couldn't connect: {e}")

    async def send_greeting(self):
        payload = {
            "type": WcpMessageType.GREETING.value,
            "version": "0",
            "commands": [],
        }
        await self.send_json(payload)

    async def send_json(self, payload: dict):
        if not self.is_connected:
            logger.error("Not connected to the server")
        message = json.dumps(payload) + "\0"
        self.writer.write(message.encode("utf-8"))
        await self.writer.drain()
        logger.info(f"Sent {payload}")

    async def listen(self):
        try:
            while self.is_connected:
                data = await self.reader.readuntil(b"\0")
                if not data:
                    break
                message = json.loads(data[:-1].decode("utf-8"))
                logger.info(f"Received {message}")
        except asyncio.IncompleteReadError:
            pass
        finally:
            self.is_connected = False

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.is_connected = False


async def main():
    client = WCPAsyncClient()
    try:
        await client.connect()
        listener_task = asyncio.create_task(client.listen())

        await client.send_greeting()
        await asyncio.sleep(2)
        await client.close()
        listener_task.cancel()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
