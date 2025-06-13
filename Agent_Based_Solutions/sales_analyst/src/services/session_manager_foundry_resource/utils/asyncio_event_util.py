# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio

class AsyncIOEventWithTimeout(asyncio.Event):
    """
    Handles asyncio events with timeout (in seconds).
    """
    async def wait(self, timeout: float) -> bool:
        """
        Waits for the asyncio.Event to be set until timeout.
        TRUE if event is successfully set, FALSE if timeout is reached
        before event set occurs.

        This method does not raise an exception.
        """
        try:
            await asyncio.wait_for(super().wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return False
        return True