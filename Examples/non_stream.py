import asyncio
import json
from api_inceptionlabs import AuthManager

async def main():
    auth = AuthManager()
    await auth.initialize_accounts()
    resp = await auth.complete_chat("lambda.mercury-coder-small", [{"role": "user", "content": "Привет!"}])
    print(json.loads(resp)["choices"][0]["message"]["content"])

asyncio.run(main())