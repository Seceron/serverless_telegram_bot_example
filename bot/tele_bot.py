import os
from datetime import datetime
import random
import re
import json

import telebot

# Read constant from environment variables available to edit at my.selectel.ru
TOKEN = os.environ.get('TOKEN')

HELP_MSG = """
Commands usage help:
/start to start
/sticker to get a sticker :-) It's so simple for now!
/getwebhook <token of your telegram bot>
/setwebhook <token of your telegram bot> <url to call on message>
"""

# Create `bot` instance to use some features from pyTelegramBotAPI package.
# WARN: Not all of them is useful in serverless architecture.
bot = telebot.TeleBot(token=TOKEN, threaded=False)
keyboard = telebot.types.ReplyKeyboardMarkup()
keyboard.row('/sticker')

def echo(message, username):
    if message.sticker:
        bot.send_message(message.chat.id, message.sticker.file_id,
                         reply_to_message_id=message.message_id)
    else:
        answer = f'Why are you write me {message.text}, {username}?'
        bot.send_message(message.chat.id, answer,
                         reply_to_message_id=message.message_id)

def start(message):
    bot.send_message(message.chat.id, "Hi! Let's start /start",
                     reply_to_message_id=message.message_id,
                     reply_markup=keyboard)

def sticker(message):
    sticker = random.choice([
        'CAACAgIAAxkBAAIL5l7ZBurScbtqAf3L8GbZw49tMULHAAJvCgACwokQSMOyShegX64nGgQ',
        'CAACAgIAAxkBAAIElV7aRMe1TAdRmePvexlAVEfT4VoAA9kFAAJ65wlI5OBBJXKTGR0aBA',
        'CAACAgIAAxkBAAIElF7aRMFtSuwYMPRI-f-P7c6Lwt9qAAI9BgACBfEQSDOvkz5SOrKDGgQ',
        'CAACAgIAAxkBAAIEml7aRjv3YCpi5j7K8jaFiUd_oYBSAAKrBQACP7AJSAdwal6DI4EUGgQ',
        'CAACAgIAAxkBAAIEnF7aRkigYLkzR5nsPFIAAU4fRIdHQAACiAcAAoOFEUjNfGM5YdTA0BoE'
    ])
    bot.send_sticker(message.chat.id, sticker,
                     reply_to_message_id=message.message_id,
                     reply_markup=keyboard)

def get_webhook_info(message, token):
    result = telebot.apihelper.get_webhook_info(token)
    webhook = telebot.types.WebhookInfo.de_json(result)
    resp = f"""
    URL: {webhook.url}
    Custom certificate: {"Yes" if webhook.has_custom_certificate else "No"}
    Last error date: {datetime.fromtimestamp(webhook.last_error_date).isoformat() if webhook.last_error_date else ""} UTC
    Last error message: "{webhook.last_error_message}"
    Max connections: {webhook.max_connections}
    Allowed updates: {webhook.allowed_updates}
    Pending update count: {webhook.pending_update_count}
    """
    bot.send_message(message.chat.id, resp,
                     reply_to_message_id=message.message_id,
                     reply_markup=keyboard)

def set_webhook_info(message, token, url):
    try:
        resp = telebot.apihelper.set_webhook(token, url, max_connections=100)
    except telebot.apihelper.ApiException as e:
        resp = str(e)
    bot.send_message(message.chat.id, json.dumps(resp, indent=2),
                     reply_to_message_id=message.message_id,
                     reply_markup=keyboard)

def route_command(command, message):
    """
    Commands router.
    """
    if command == '/start':
        return start(message)
    elif command == '/sticker':
        return sticker(message)
    else:
        match = re.search(r'/setwebhook\s(\d+:[a-zA-Z0-9-]+)\s(https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+/.*)', message.text)
        if match and match[1] and match[2]:
            return set_webhook_info(message, token=match[1], url=match[2])
        match = re.search(r'/getwebhook\s(\d+:[a-zA-Z0-9-]+)', message.text)
        if match and match[1]:
            return get_webhook_info(message, token=match[1])
    bot.send_message(message.chat.id, "Unknown command, sorry. " + HELP_MSG,
                     reply_to_message_id=message.message_id,
                     reply_markup=keyboard)

def main(**kwargs):
    """
    Serverless environment entry point.
    """
    print(f'Received: "{kwargs}"')
    message = telebot.types.Update.de_json(kwargs)
    message = message.message
    if message.text and message.text[0] == '/':
        print(f'Echo on "{message.text}"')
        route_command(message.text.lower(), message)
    else:
        echo(message, message.chat.username)
