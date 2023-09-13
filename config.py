import os

from dotenv import load_dotenv

local_env = 'M:\projects\environments\ReminderBot\.env'

if os.path.exists(local_env):
    load_dotenv(local_env)

TOKEN = os.getenv('TOKEN')

