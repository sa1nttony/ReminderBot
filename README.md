<br />
<div align="center">
  <img src="ReminderBot_logo.png" alt="Logo" width="80" height="80">
  <h3 align="center">Reminder_Bot</h3>
  <p align="center">
    A bot that helps not to forget about important events
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

The purpose of this bot is to remind about important events of both one person and a group of people.

The differences between this bot and the built-in telegram function of reminders and deferred messages are as follows:
1. Reminders are executed several times: a day, two hours and at the time of the event
2. The user is required to confirm that the reminder task has been completed, otherwise the task is postponed for an hour later
3. It is possible to easily move the date and time of the event to any time without changing the other parameters of the task
4. In the future, the addition of a web application that allows you to view and edit user tasks in real time, and tasks given by the user for other group members


<!-- GETTING STARTED -->
## Getting Started

The bot is not ready yet, so I won't be able to share a working link, but you can try using the bot yourself

### Prerequisites
For correct work you need to install several packages:
  ```sh
  pip3 install apscheduler
  pip3 install pyTelegramBotAPI
  pip3 python-dotenv
  ```

### Installation

A couple more steps to launch the bot:

1. Register bot with <a href="https://t.me/BotFather">@BotFather</a> and get API Key. For more information see <a href="https://core.telegram.org/bots/features#botfather">oficial documentation</a>
2. Clone the repo
   ```sh
   git clone https://github.com/sa1nttony/ReminderBot
   ```
3. in the same directory with the project folder, create folder `environments\ReminderBot` and create a `.env` file in it
   ```sh
   \---environment
   |   \---ReminderBot
   |   |   +---.env
   +---ReminderBot
   ```
4. Enter your API Key in `.env`
   ```js
   TOKEN = 'your API Key here'
   ```
5. Run `db_initial.py` in any IDE to make your own database
6. Run `app.py` in any IDE


<!-- USAGE EXAMPLES -->
## Usage

1. Send `/init` to bot, for initial your account
2. Send `/new_task` to add new task

The bot can be used in group chats. To assign a task to another chat user, you need to get the administrator status with the command `/admin`
The user to whom you are giving the task must also be initialized


<!-- ROADMAP -->
## Roadmap

- [x] Add the ability to create and store tasks
- [x] Add the ability to work in a group chat
- [ ] Add the ability to edit and delete tasks
- [ ] Add the ability to output user tasks on request
- [ ] Add the ability to receive notifications about tasks
- [ ] Create a web application with the ability to create, edit, delete and view your tasks and tasks to other users


<!-- CONTACT -->
## Contact

Feel free to give any tips, how i can make my code better

Telegram: [@sa1nttony](https://t.me/sa1nttony)

Email: [sa1ntholytony@yandex.ru](mailto:sa1ntholytony@yandex.ru)
