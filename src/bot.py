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
    query = update.callback_query
    bot = context.bot
    ids = json.loads(query.data)
    category_id = ids['category_id']
    product_id = ids['product_id']

    chat_id = update.effective_chat.id
    user = update.effective_user
    print(user)
    if chat_id in basket:
        if user.id in basket[chat_id]:
            if category_id in basket[chat_id][user.id]:
                if product_id in basket[chat_id][user.id][category_id]:
                    basket[chat_id][user.id][category_id][product_id] += 1
                else:
                    basket[chat_id][user.id][category_id][product_id] = 1
            else:
                basket[chat_id][user.id][category_id] = {product_id: 1}
        else:
            basket[chat_id][user.id] = {'username': user.username,
                                        'first_name': user.first_name,
                                        category_id: {product_id: 1}}
    else:
        basket[chat_id] = {user.id: {'username': user.username,
                                     'first_name': user.first_name,
                                     category_id: {product_id: 1}}}

    print(basket)
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text='Added ' + menu[category_id]['products'][product_id][
                              'name'] + ' to your basket!')

    return ConversationHandler.END


def remove_from_basket(update, context):
    return FIRST


def show_basket(update, context):
    bot = context.bot
    query = update.callback_query

    chat_id = update.effective_chat.id
    user = update.effective_user

    message_and_price = user_basket(basket[chat_id][user.id])

    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=message_and_price['message'])

    return ConversationHandler.END


def user_basket(basket):
    price_basket = 0.0
    message = ""

    for category_id in basket.keys():
        for product_id in basket[category_id].keys():
            amount = basket[category_id][product_id]
            name = menu[category_id]['products'][product_id]['name']
            price_str = menu[category_id]['products'][product_id]['price']
            price = float(price_str.replace(' €', '').replace(',', '.'))

            price_basket += price * amount
            print(price_basket)
            message = message + str(amount) + "x " + name + " " + price_str + "\n"

    message = message + "Sum: " + str(price_basket) + " €"

    return {'message': message, 'price': price_basket}


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
