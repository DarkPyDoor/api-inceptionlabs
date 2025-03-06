import multiprocessing

TOKEN_TTL = 6 * 60 * 60
PRE_EXPIRY_THRESHOLD = 1 * 60 * 60
MAX_WORKERS = max(2, multiprocessing.cpu_count() // 2)

# Значения по умолчанию, которые будут переопределяться из cli.py
API_HOST = "0.0.0.0"
API_PORT = 5001
DEFAULT_MODEL = "lambda.mercury-coder-small"
MIN_ACCOUNTS = 2

def update_config(**kwargs):
    global API_HOST, API_PORT, DEFAULT_MODEL, MIN_ACCOUNTS
    API_HOST = kwargs.get('host', API_HOST)
    API_PORT = kwargs.get('port', API_PORT)
    DEFAULT_MODEL = kwargs.get('default_model', DEFAULT_MODEL)
    MIN_ACCOUNTS = kwargs.get('min_accounts', MIN_ACCOUNTS)