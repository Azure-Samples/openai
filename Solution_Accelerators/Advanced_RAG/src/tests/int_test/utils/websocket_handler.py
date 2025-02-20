import asyncio
import json
import uuid

import websockets
from retry import retry


class WebSocketHandler:
    def __init__(self, url: str, logger, connection_id=None, scenario="rag"):
        self.url = url.replace("http", "ws") if url.startswith("http") else url.replace("https", "wss")
        self.connection_id = connection_id
        self.handler = None
        self.logger = logger
        self.scenario = scenario

    async def connect(self):
        self.connection_id = str(uuid.uuid4()) if not self.connection_id else self.connection_id
        self.handler = await websockets.connect(
            f"{self.url}/ws/chat?connection_id={self.connection_id}&scenario={self.scenario}"
        )

    async def send(self, message):
        message["connection_id"] = self.connection_id
        print(f"Sending message: {message}")
        await self.handler.send(json.dumps(message))

    async def receive(self):
        response = await self.handler.recv()
        return json.loads(response)

    # @retry(tries=5, delay=60, backoff=1.1)
    async def send_and_receive(self, message, max_retries=3, retry_delay=5):
        self.logger.info("Attempting to send and receive message")
        retries = 0

        while retries < max_retries:
            try:
                await self.connect()
                await asyncio.sleep(5)
                await self.send(message)

                async def receive_with_timeout():
                    while True:
                        response = await self.receive()
                        if response.get("answer", {}).get("answer_string") and response.get("answer", {}).get(
                            "data_points"
                        ):
                            return response

                try:
                    response = await asyncio.wait_for(
                        receive_with_timeout(), timeout=120
                    )  # TODO: Make timeout configurable?
                    return response
                except asyncio.TimeoutError:
                    raise TimeoutError("Timeout: Session manager did not respond in 120 seconds")
                except ConnectionError as e:
                    self.logger.error(f"Connection error during receive: {e}")
                    retries += 1
                    if retries < max_retries:
                        self.logger.info(f"Retrying... ({retries}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                    else:
                        self.logger.error("Max retries reached. Giving up.")
                        raise

            except ConnectionError as e:
                self.logger.error(f"Connection error during initial connection: {e}")
                retries += 1
                if retries < max_retries:
                    self.logger.info(f"Retrying... ({retries}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                else:
                    self.logger.error("Max retries reached. Giving up.")
                    raise

            finally:
                await self.close()

    async def close(self):
        if self.handler:
            await self.handler.close()
