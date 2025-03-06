import argparse
from .api import run_api

def main():
    parser = argparse.ArgumentParser(description="Run Chat Library API")
    parser.add_argument('--port', type=int, default=5001, help="Port to run the API on")
    parser.add_argument('--host', type=str, default="0.0.0.0", help="Host to run the API on")
    parser.add_argument('--model', type=str, default="lambda.mercury-coder-small", help="Default model for API")
    parser.add_argument('--min-accounts', type=int, default=2, help="Minimum number of accounts to maintain")
    args = parser.parse_args()
    
    # Передаём аргументы в run_api
    run_api(port=args.port, host=args.host, default_model=args.model, min_accounts=args.min_accounts)

if __name__ == "__main__":
    main()