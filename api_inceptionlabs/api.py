from flask import Flask, request, Response, jsonify
import json
import asyncio
from .auth_manager import AuthManager
from .config import API_HOST, API_PORT, DEFAULT_MODEL, MIN_ACCOUNTS, update_config

def create_app():
    app = Flask(__name__)
    auth_manager = AuthManager()
    
    # Запускаем инициализацию аккаунтов в фоновом режиме
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(auth_manager.initialize_accounts())
    
    @app.route('/api/chat/completions', methods=['POST'])
    def chat_completions():
        data = request.json
        model = data.get('model', DEFAULT_MODEL)
        messages = data.get('messages', [])
        stream = data.get('stream', False)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            if stream:
                print("Processing stream request...")
                return Response(generate_stream(auth_manager, model, messages, loop),
                                content_type='text/event-stream',
                                headers={'X-Accel-Buffering': 'no'})
            else:
                print("Processing non-stream request...")
                response_text = loop.run_until_complete(auth_manager.complete_chat(model, messages))
                return jsonify(json.loads(response_text))
        except Exception as e:
            print(f"Error in chat_completions: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            if not stream:
                loop.close()

    def generate_stream(auth_manager, model, messages, loop):
        async def stream():
            async for chunk in auth_manager.stream_chat(model, messages):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        async_gen = stream()
        while True:
            try:
                yield loop.run_until_complete(anext(async_gen))
            except StopAsyncIteration:
                loop.close()
                break

    return app

def run_api(port=API_PORT, host=API_HOST, default_model=DEFAULT_MODEL, min_accounts=MIN_ACCOUNTS):
    update_config(port=port, host=host, default_model=default_model, min_accounts=min_accounts)
    app = create_app()
    print(f"API running at http://{API_HOST}:{port}/api/chat/completions")
    print(f"Docs: http://{API_HOST}:{port}/docs (not implemented yet)")
    app.run(host=API_HOST, port=port, debug=False, use_reloader=False)