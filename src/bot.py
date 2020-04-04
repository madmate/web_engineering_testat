"""
Prototype Chatbot for a telegram group based delivery service order
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

cart = dict()
all_user_data = dict()
# callback_data as pattern for the ConversationHandler
ONE, TWO, THREE, FOUR, FIVE, SIX = range(6)
# stages for the ConversationHandler
FIRST, SECOND, THIRD, FOURTH, FIFTH, SIXTH, SEVENTH = range(7)


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


def add_to_cart(update, context):
    query = update.callback_query
    bot = context.bot
    ids = json.loads(query.data)
    category_id = ids['category_id']
    product_id = ids['product_id']

    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id in cart:
        if user.id in cart[chat_id]:
            if category_id in cart[chat_id][user.id]:
                if product_id in cart[chat_id][user.id][category_id]:
                    cart[chat_id][user.id][category_id][product_id] += 1
                else:
                    cart[chat_id][user.id][category_id][product_id] = 1
            else:
                cart[chat_id][user.id][category_id] = {product_id: 1}
        else:
            cart[chat_id][user.id] = {category_id: {product_id: 1}}
    else:
        cart[chat_id] = {user.id: {category_id: {product_id: 1}}}

    keyboard = [[InlineKeyboardButton("order more", callback_data=str(TWO))],
                [InlineKeyboardButton("back to menu", callback_data=str(ONE))]]

    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text='Added ' + menu[category_id]['products'][product_id][
                              'name'] + ' to your order!',
                          reply_markup=InlineKeyboardMarkup(keyboard))

    return SEVENTH


def cart_inline_keyboard(update, context):
    bot = context.bot
    query = update.callback_query

    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id in cart.keys():
        if user.id in cart[chat_id].keys():
            user_cart = cart[chat_id][user.id]
            keyboard = []

            for category_id in user_cart.keys():
                for product_id in user_cart[category_id].keys():
                    amount = user_cart[category_id][product_id]
                    name = menu[category_id]['products'][product_id]['name']
                    price = menu[category_id]['products'][product_id]['price']

                    keyboard.append([InlineKeyboardButton(str(amount) + "x " + name + " " + price,
                                                          callback_data=json.dumps({"category_id": category_id,
                                                                                    "product_id": product_id}))])

            keyboard.append([InlineKeyboardButton("Remove all products",
                                                  callback_data=json.dumps({"category_id": category_id,
                                                                            "product_id": -1}))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text="Select product to remove from cart:",
                                  reply_markup=reply_markup)
            return FOURTH

    keyboard = [[InlineKeyboardButton("back to menu", callback_data=str(ONE))]]
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text="No products in your cart!",
                          reply_markup=InlineKeyboardMarkup(keyboard))
    return SEVENTH


def remove_from_cart(update, context):
    bot = context.bot
    query = update.callback_query

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    ids = json.loads(query.data)
    category_id = ids['category_id']
    product_id = ids['product_id']

    if product_id == -1:
        del cart[chat_id][user_id]
        if not bool(cart[chat_id]):
            del cart[chat_id]
        message = "All products removed from your cart!"
    else:
        if cart[chat_id][user_id][category_id][product_id] > 1:
            cart[chat_id][user_id][category_id][product_id] -= 1
        else:
            del cart[chat_id][user_id][category_id][product_id]
            if not bool(cart[chat_id][user_id][category_id]):
                del cart[chat_id][user_id][category_id]
            if not bool(cart[chat_id][user_id]):
                del cart[chat_id][user_id]
            if not bool(cart[chat_id]):
                del cart[chat_id]
        message = "Removed " + menu[category_id]['products'][product_id]['name'] + "from your cart. Your " \
                                                                                   "cart: \n" + \
                  str_user_cart(chat_id, user_id)['message']

    keyboard = [[InlineKeyboardButton("remove more", callback_data=str(THREE))],
                [InlineKeyboardButton("back to menu", callback_data=str(ONE))]]

    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=message,
                          reply_markup=InlineKeyboardMarkup(keyboard))
    return SEVENTH


def show_cart(update, context):
    bot = context.bot
    query = update.callback_query

    chat_id = update.effective_chat.id
    user = update.effective_user

    message_and_price = str_user_cart(chat_id, user.id)

    keyboard = [[InlineKeyboardButton("back to menu", callback_data=str(ONE))]]
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=message_and_price['message'],
                          reply_markup=InlineKeyboardMarkup(keyboard))

    return SEVENTH


def str_user_cart(chat_id, user_id):
    price_cart = 0.0
    message = ""

    if chat_id in cart.keys():
        if user_id in cart[chat_id].keys():
            cart_from_user = cart[chat_id][user_id]
            for category_id in cart_from_user.keys():
                for product_id in cart_from_user[category_id].keys():
                    amount = cart_from_user[category_id][product_id]
                    name = menu[category_id]['products'][product_id]['name']
                    price = float(menu[category_id]['products'][product_id]['price'].replace(' €', ''))

                    price_cart += price * amount
                    message = message + str(amount) + "x " + name + " " + str(f'{price:.2f}') + " €" + "\n"

            message = message + "Sum: " + str(f'{price_cart:.2f}') + " €\n"
            return {'message': message, 'price': price_cart}
    message = "no items in cart\n"
    return {'message': message, 'price': price_cart}


def str_group_cart(chat_id):
    message = ''
    chat_sum = 0.0

    if chat_id in cart.keys():
        for user_id in cart[chat_id].keys():
            user = all_user_data[user_id]

            message = message + str(user.username) + " aka " + str(user.first_name) + ":\n"
            message_and_price = str_user_cart(chat_id, user_id)
            chat_sum += message_and_price['price']
            message = message + message_and_price['message']

        message = message + "Chat Sum: " + str(f'{chat_sum:.2f}') + " €"
    else:
        message = "No orders made in this group chat!"

    return message


def show_group_cart(update, context):
    bot = context.bot
    query = update.callback_query
    chat_id = update.effective_chat.id

    keyboard = [[InlineKeyboardButton("back to menu", callback_data=str(ONE))]]
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=str_group_cart(chat_id),
                          reply_markup=InlineKeyboardMarkup(keyboard))

    return SEVENTH


def finish_question(update, context):
    bot = context.bot
    query = update.callback_query
    chat_id = update.effective_chat.id
    if chat_id in cart.keys():
        keyboard = [[InlineKeyboardButton("yes", callback_data="yes"), InlineKeyboardButton("no", callback_data="no")],
                    [InlineKeyboardButton("no, back to menu please", callback_data="menu")]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text="Are you sure you want to finalize the order for this chat?",
                              reply_markup=reply_markup)
        return SIXTH

    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text="No orders made in this group chat!")
    return ConversationHandler.END


def finish(update, context):
    bot = context.bot
    query = update.callback_query
    chat_id = update.effective_chat.id
    message = "Finalized your order. Pay and order at Izmir based on the following message:\n" + str_group_cart(chat_id)
    del cart[chat_id]
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=message)
    return ConversationHandler.END


def clear_all_question(update, context):
    bot = context.bot
    query = update.callback_query
    keyboard = [[InlineKeyboardButton("yes", callback_data="yes"), InlineKeyboardButton("no", callback_data="no")],
                [InlineKeyboardButton("no, back to menu please", callback_data="menu")]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text="Are you sure you want to delete all orders made in this chat?",
                          reply_markup=reply_markup)
    return FIFTH


def clear_all(update, context):
    bot = context.bot
    query = update.callback_query
    chat_id = update.effective_chat.id

    if query.data == "yes":
        if chat_id in cart:
            del cart[chat_id]
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text="Deleted all orders for this chat!")
        return ConversationHandler.END
    if query.data == "no":
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text="Nothing changed!")
        return ConversationHandler.END
    if query.data == "menu":
        reply_markup = start_menu()
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text="What do you want to do?",
                              reply_markup=reply_markup)
        return FIRST


def start_menu():
    keyboard = [[InlineKeyboardButton("add food to cart", callback_data=str(ONE))],
                [InlineKeyboardButton("remove food from cart", callback_data=str(TWO))],
                [InlineKeyboardButton("your cart", callback_data=str(THREE))],
                [InlineKeyboardButton("group cart", callback_data=str(FOUR))],
                [InlineKeyboardButton("send order for group", callback_data=str(FIVE))],
                [InlineKeyboardButton("clear all orders from chat", callback_data=str(SIX))]]

    return InlineKeyboardMarkup(keyboard)


def start_over(update, context):
    bot = context.bot
    query = update.callback_query
    reply_markup = start_menu()
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text="What do you want to do?",
                          reply_markup=reply_markup)
    return FIRST


def start(update, context):
    put_in_all_user_data(update.effective_user)

    reply_markup = start_menu()
    update.message.reply_text("What do you want to do?", reply_markup=reply_markup)

    return FIRST


def put_in_all_user_data(user):
    all_user_data[user.id] = user


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
                    CallbackQueryHandler(cart_inline_keyboard, pattern='^' + str(TWO) + '$'),
                    CallbackQueryHandler(show_cart, pattern='^' + str(THREE) + '$'),
                    CallbackQueryHandler(show_group_cart, pattern='^' + str(FOUR) + '$'),
                    CallbackQueryHandler(finish_question, pattern='^' + str(FIVE) + '$'),
                    CallbackQueryHandler(clear_all_question, pattern='^' + str(SIX) + '$')],
            SECOND: [CallbackQueryHandler(show_category)],
            THIRD: [CallbackQueryHandler(add_to_cart)],
            FOURTH: [CallbackQueryHandler(remove_from_cart)],
            FIFTH: [CallbackQueryHandler(clear_all)],
            SIXTH: [CallbackQueryHandler(finish)],
            SEVENTH: [CallbackQueryHandler(start_over, pattern='^' + str(ONE) + '$'),
                      CallbackQueryHandler(show_categories, pattern='^' + str(TWO) + '$'),
                      CallbackQueryHandler(cart_inline_keyboard, pattern='^' + str(THREE) + '$')]

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
