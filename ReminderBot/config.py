import os

from dotenv import load_dotenv

os.chdir('../../')
os.chdir(os.path.join('environments', 'ReminderBot'))


local_env = os.path.join(os.getcwd(), '.env')

if os.path.exists(local_env):
    load_dotenv(local_env)

TOKEN = os.getenv('TOKEN')
