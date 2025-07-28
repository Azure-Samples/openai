# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import time
from typing import List, Optional, Any
from pydantic import BaseModel


class LogProperties(BaseModel):
    application_name: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    dialog_id: Optional[str] = None
    request: Optional[str] = None
    response: Optional[str] = None
    duration_ms: Optional[float] = -1.0
    start_time: Optional[float] = -1.0
    path: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.start_time = time.monotonic()

    def set_start_time(self):
        self.start_time = time.monotonic()

    def calculate_duration_ms(self):
        return (time.monotonic() - self.start_time) * 1000

    def model_dump(self):
        properties = {}
        if self.application_name:
            properties["ApplicationName"] = self.application_name
        if self.user_id:
            properties["user_id"] = self.user_id
        if self.conversation_id:
            properties["conversation_id"] = self.conversation_id
        if self.dialog_id:
            properties["dialog_id"] = self.dialog_id
        if self.request:
            properties["request"] = self.request
        if self.response:
            properties["response"] = self.response
        if self.path:
            properties["path"] = self.path
        properties["duration_ms"] = self.duration_ms
        return properties

    def record_duration_ms(self):
        self.duration_ms = (time.monotonic() - self.start_time) * 1000


class HttpRequestLog(LogProperties):
    request_url: Optional[str] = "Not set"
    method: Optional[str] = "Not set"
    status_code: Optional[int] = -1

    def __init__(self, **data):
        super().__init__(**data)

    def model_dump(self):
        properties = super().model_dump()
        properties["request_url"] = self.request_url
        properties["method"] = self.method
        return properties
