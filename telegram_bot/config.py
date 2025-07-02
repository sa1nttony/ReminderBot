import os

from pathlib import Path
from dotenv import load_dotenv

local_env = Path(__file__).parent.parent / 'environments' / '.env'

if os.path.exists(local_env):
    load_dotenv(local_env)

TOKEN = os.getenv('TOKEN')


if __name__ == '__main__':
    print(TOKEN)