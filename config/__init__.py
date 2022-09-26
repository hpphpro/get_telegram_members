import os
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(raise_error_if_not_found=True))



API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')

if not all(API_ID, API_HASH):
    raise AttributeError('API_ID and API_HASH is required')

ROOT_DIR = Path(__file__).resolve().parent.parent

source_path = ROOT_DIR / 'source'
