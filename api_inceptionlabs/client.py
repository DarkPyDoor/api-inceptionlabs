import asyncio
import json
import time
import brotli
from .auth_manager import AuthManager
from .config import DEFAULT_MODEL

class Completions:
    def __init__(self, client):
        self.client = client

    async def create(self, model=DEFAULT_MODEL, messages=None, **kwargs):
        response = await self.client._complete_chat(model, messages or [])
        return CompletionResponse(response, model)

    async def stream(self, model=DEFAULT_MODEL, messages=None, **kwargs):
        return self.client._stream_chat(model, messages or [])

class Chat:
    def __init__(self, client):
        self.completions = Completions(client)

class CompletionResponse:
    def __init__(self, response, model):
        self.raw_response = response
        self.choices = [
            Choice(
                message=Message(role="assistant", content=self._extract_content()),
                index=0,
                finish_reason="stop"
            )
        ]
        self.created = int(time.time())
        self.id = f"chatcmpl-{self.created}"
        self.model = model
        self.object = "chat.completion"

    def _extract_content(self):
        if self.raw_response.status != 200:
            return self.raw_response.content.decode('utf-8')
        content_encoding = self.raw_response.headers.get('Content-Encoding', '').lower()
        try:
            content = self.raw_response.content.decode('utf-8')
            if content_encoding == 'br':
                content = brotli.decompress(self.raw_response.content).decode('utf-8')
            return json.loads(content)["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError) as e:
            return content

class StreamChunk:
    def __init__(self, chunk, model):
        delta_content = self._extract_delta_content(chunk)
        self.choices = [
            Choice(
                message=Message(role="assistant", content=delta_content),
                index=0,
                finish_reason=chunk["choices"][0].get("finish_reason") if "choices" in chunk else None
            )
        ] if delta_content else []
        self.id = chunk.get("id", f"chatcmpl-{int(time.time())}")
        self.model = model
        self.object = "chat.completion.chunk"

    def _extract_delta_content(self, chunk):
        try:
            if "choices" in chunk and chunk["choices"]:
                if isinstance(chunk["choices"][0]["delta"], str):
                    return chunk["choices"][0]["delta"]
                return chunk["choices"][0]["delta"].get("content")
            return chunk["choices"][0]["delta"] if "choices" in chunk else None
        except (KeyError, IndexError):
            return None

class Choice:
    def __init__(self, message, index, finish_reason):
        self.message = message
        self.index = index
        self.finish_reason = finish_reason
        self.delta = Delta(content=message.content)

class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content

class Delta:
    def __init__(self, content):
        self.content = content

class AsyncClient:
    def __init__(self, auth_manager=None):
        self.auth_manager = auth_manager or AuthManager()
        self.chat = Chat(self)

    async def _complete_chat(self, model, messages):
        return await self.auth_manager.complete_chat(model, messages)

    async def _stream_chat(self, model, messages):
        async for chunk in self.auth_manager.stream_chat(model, messages):
            yield StreamChunk(chunk, model)