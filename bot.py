#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards.
"""
import json
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

from os.path import join, dirname
from dotenv import load_dotenv

from parser import get_menu

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

url = 'https://www.izmir-kebap-friedrichshafen.de'
print(get_menu(url))
menu = json.loads(get_menu(url))
print(menu)


def start(update, context):
    keyboard = []
    for category_id in menu.keys():
        keyboard.append([InlineKeyboardButton(str(menu[category_id]['category']),
                                              callback_data=json.dumps({"category_id": category_id,
                                                                        "product_id": 00}))])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose :', reply_markup=reply_markup)


def button(update, context):
    query = update.callback_query
    ids = json.loads(query.data)
    category_id = ids['category_id']
    product_id = ids['product_id']
    keyboard = []

    products = menu[category_id]['products']
    for product_id in products.keys():
        product = products[product_id]
        keyboard.append([InlineKeyboardButton(product['name'] + " " + product['price'], callback_data=str(product_id))])

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text('Select desired food in ' + menu[category_id]['category'] + ":", reply_markup=reply_markup)


def help(update, context):
    update.message.reply_text("Use /start to test this bot.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # load dotenv as environment   variable
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(os.environ.get("BOT_API_TOKEN"), use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()