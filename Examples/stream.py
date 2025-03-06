import asyncio
import json
from api_inceptionlabs import AuthManager

async def main():
    auth = AuthManager()
    await auth.initialize_accounts()
    async for chunk in auth.stream_chat("lambda.mercury-coder-small", [{"role": "user", "content": "Привет!"}]):
        if isinstance(chunk, dict) and "choices" in chunk:
            delta = chunk["choices"][0]["delta"]
            content = delta.get("content", "") if isinstance(delta, dict) else delta
            if content:
                print(content, end="")
        else:
            print(f"Error chunk: {chunk}")

asyncio.run(main())