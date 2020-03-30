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
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler

from os.path import join, dirname
from dotenv import load_dotenv

from src.parser import get_menu

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

url = 'https://www.izmir-kebap-friedrichshafen.de'
menu = json.loads(get_menu(url))
print(menu)
basket = {}

ONE, TWO, THREE, FOUR, FIVE = range(5)

FIRST, SECOND, THIRD = range(3)


def show_categories(update, context):
    query = update.callback_query
    bot = context.bot

    keyboard = []
    for category_id in menu.keys():
        keyboard.append([InlineKeyboardButton(str(menu[category_id]['category']),
                                              callback_data=json.dumps({"category_id": category_id,
                                                                        "product_id": 0}))])

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text='Please choose :',
                          reply_markup=reply_markup)

    return SECOND


def show_category(update, context):
    query = update.callback_query
    bot = context.bot
    ids = json.loads(query.data)
    category_id = ids['category_id']
    keyboard = []

    products = menu[category_id]['products']
    for product_id in products.keys():
        product = products[product_id]
        keyboard.append([InlineKeyboardButton(product['name'] + " " + product['price'],
                                              callback_data=json.dumps({"category_id": category_id,
                                                                        "product_id": product_id}))])

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text='Select desired food in ' + menu[category_id]['category'] + ":",
                          reply_markup=reply_markup)

    return THIRD


def add_to_basket(update, context):
    print(update)
    query = update.callback_query
    bot = context.bot
    ids = json.loads(query.data)
    category_id = ids['category_id']
    product_id = ids['product_id']

    group_id = query.message.chat_id
    print(group_id)
    user = update.effective_user
    print(user)
    if group_id in basket:
        print(1)
        if user.id in basket[group_id]:
            print(2)
            if product_id in basket[group_id][user.id]:
                print(3)
                basket[group_id][user.id][product_id] += 1
            else:
                basket[group_id][user.id][product_id] = 1
        else:
            basket[group_id][user.id] = {product_id: 1}
    else:
        print(4)
        basket[group_id] = {user.id: {product_id: 1}}

    print(basket)

    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text='Added ' + menu[category_id]['products'][product_id][
                              'name'] + ' to your basket!')


def remove_from_basket(update, context):
    return FIRST


def show_basket(update, context):
    return FIRST


def show_group_basket(update, context):
    return FIRST


def finish(update, context):
    return FIRST


def clear_all(update, context):
    return FIRST


def start(update, context):
    keyboard = [[InlineKeyboardButton("Add to Basket", callback_data=str(ONE))],
                [InlineKeyboardButton("Remove from Basket", callback_data=str(TWO))],
                [InlineKeyboardButton("Your Order", callback_data=str(THREE))],
                [InlineKeyboardButton("Group Order", callback_data=str(FOUR))],
                [InlineKeyboardButton("Finish", callback_data=str(FIVE))]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("What do you want to do?", reply_markup=reply_markup)

    return FIRST


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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST: [CallbackQueryHandler(show_categories, pattern='^' + str(ONE) + '$'),
                    CallbackQueryHandler(remove_from_basket, pattern='^' + str(TWO) + '$'),
                    CallbackQueryHandler(show_basket, pattern='^' + str(THREE) + '$'),
                    CallbackQueryHandler(show_group_basket, pattern='^' + str(FOUR) + '$'),
                    CallbackQueryHandler(finish, pattern='^' + str(FIVE) + '$')],
            SECOND: [CallbackQueryHandler(show_category)],
            THIRD: [CallbackQueryHandler(add_to_basket)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
