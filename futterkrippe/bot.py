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

from futterkrippe.parser import get_menu

# basic logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# url of menu from delivery service
url = 'https://www.izmir-kebap-friedrichshafen.de'
# requests menu in json from parser und loads it as Python Dictionary
menu = json.loads(get_menu(url))

# storage for all orders made
cart = dict()
# storage for user data from every user which writes with the bot
all_user_data = dict()
# callback_data as pattern for the ConversationHandler
ONE, TWO, THREE, FOUR, FIVE, SIX = range(6)
# stages for the ConversationHandler
FIRST, SECOND, THIRD, FOURTH, FIFTH, SIXTH, SEVENTH = range(7)


def show_categories(update, context):
    """show all categories on menu as InlineKeyBoardButton

    category id is given as callback_data"""
    query = update.callback_query
    bot = context.bot

    keyboard = []
    # iterate over every category
    for category_id in menu.keys():
        # add category to keyboard
        keyboard.append([InlineKeyboardButton(str(menu[category_id]['category']),
                                              callback_data=json.dumps({"category_id": category_id,
                                                                        "product_id": 0}))])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # edits last message to keyboard with all categories
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text='Please choose :',
                          reply_markup=reply_markup)
    # notify ConversationHandler of SECOND stage
    return SECOND


def show_category(update, context):
    """shows all product from one category

    category is selected in :func:`show_categories` and given as callback_data"""
    query = update.callback_query
    bot = context.bot
    # loads json received from callback_data into dictionary
    ids = json.loads(query.data)
    category_id = ids['category_id']
    keyboard = []

    products = menu[category_id]['products']
    # iterates over all products in selected category
    for product_id in products.keys():
        product = products[product_id]
        # add each product to keyboard with id information as callback_data
        keyboard.append([InlineKeyboardButton(product['name'] + " " + product['price'],
                                              callback_data=json.dumps({"category_id": category_id,
                                                                        "product_id": product_id}))])

    reply_markup = InlineKeyboardMarkup(keyboard)
    # edits last message to keyboard with all products from category
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text='Select desired food in ' + menu[category_id]['category'] + ":",
                          reply_markup=reply_markup)
    # notify ConversationHandler of THIRD stage
    return THIRD


def add_to_cart(update, context):
    """adds selected product to card

    handles respones of :func:`show_category`"""
    query = update.callback_query
    bot = context.bot
    # loads json received from callback_data into dictionary
    ids = json.loads(query.data)
    category_id = ids['category_id']
    product_id = ids['product_id']

    chat_id = update.effective_chat.id
    user = update.effective_user
    # checks if chat already made an order
    if chat_id in cart:
        # checks if user already made an order
        if user.id in cart[chat_id]:
            # checks user already ordered from category
            if category_id in cart[chat_id][user.id]:
                # checks if user already ordered product
                if product_id in cart[chat_id][user.id][category_id]:
                    # increase count how often product was ordered
                    cart[chat_id][user.id][category_id][product_id] += 1
                else:
                    cart[chat_id][user.id][category_id][product_id] = 1
            else:
                cart[chat_id][user.id][category_id] = {product_id: 1}
        else:
            cart[chat_id][user.id] = {category_id: {product_id: 1}}
    else:
        cart[chat_id] = {user.id: {category_id: {product_id: 1}}}

    # option to order more or go back to start menu
    keyboard = [[InlineKeyboardButton("order more", callback_data=str(TWO))],
                [InlineKeyboardButton("back to menu", callback_data=str(ONE))]]

    # add last message text to product ordered
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text='Added ' + menu[category_id]['products'][product_id][
                              'name'] + ' to your order!',
                          reply_markup=InlineKeyboardMarkup(keyboard))

    return SEVENTH


def cart_inline_keyboard(update, context):
    """replies keyboard with all orders made by users and option to delete all"""
    bot = context.bot
    query = update.callback_query

    chat_id = update.effective_chat.id
    user = update.effective_user

    # check if chat made any orders
    if chat_id in cart.keys():
        # check if user made any orders
        if user.id in cart[chat_id].keys():
            user_cart = cart[chat_id][user.id]
            keyboard = []

            # iterate through every category
            for category_id in user_cart.keys():
                # iterate through every product ordered in that category
                for product_id in user_cart[category_id].keys():
                    amount = user_cart[category_id][product_id]
                    name = menu[category_id]['products'][product_id]['name']
                    price = menu[category_id]['products'][product_id]['price']
                    # add product to list of items ordered with id's as callback data
                    keyboard.append([InlineKeyboardButton(str(amount) + "x " + name + " " + price,
                                                          callback_data=json.dumps({"category_id": category_id,
                                                                                    "product_id": product_id}))])
            # option to remove all products from user cart with negative id's
            keyboard.append([InlineKeyboardButton("Remove all products",
                                                  callback_data=json.dumps({"category_id": -1,
                                                                            "product_id": -1}))])

            reply_markup = InlineKeyboardMarkup(keyboard)  #
            # edit last message send by bot
            bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text="Select product to remove from cart:",
                                  reply_markup=reply_markup)
            # notify ConversationHandler of FOURTH stage
            return FOURTH

    # edit last message to notification that the user ordered no products and add a Button back to start menu
    keyboard = [[InlineKeyboardButton("back to menu", callback_data=str(ONE))]]
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text="No products in your cart!",
                          reply_markup=InlineKeyboardMarkup(keyboard))
    # notify ConversationHandler of SEVENTH stage
    return SEVENTH


def remove_from_cart(update, context):
    """removes one or all products ordered by user from cart

    response to option selected in :func:`cart_inline_keyboard`"""
    bot = context.bot
    query = update.callback_query

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # loads json received from callback_data into dictionary
    ids = json.loads(query.data)
    category_id = ids['category_id']
    product_id = ids['product_id']

    # user selected to remove all products from cart
    if product_id == -1:
        # delete user from cart
        del cart[chat_id][user_id]
        # when no other orders where made in this group chat also delete group from cart
        if not bool(cart[chat_id]):
            del cart[chat_id]
        message = "All products removed from your cart!"
    # user selected product
    else:
        # reduce the quantity when there is more than one order for this product
        if cart[chat_id][user_id][category_id][product_id] > 1:
            cart[chat_id][user_id][category_id][product_id] -= 1
        else:
            # delete product
            del cart[chat_id][user_id][category_id][product_id]
            # delete category when no other products where ordered in this category by user
            if not bool(cart[chat_id][user_id][category_id]):
                del cart[chat_id][user_id][category_id]
                # delete user when no other products where ordered by user
                if not bool(cart[chat_id][user_id]):
                    del cart[chat_id][user_id]
                    # delete group when no no other users ordered in group chat
                    if not bool(cart[chat_id]):
                        del cart[chat_id]
        message = "Removed " + menu[category_id]['products'][product_id]['name'] + "from your cart. Your " \
                                                                                   "cart: \n" + \
                  str_user_cart(chat_id, user_id)['message']
    # InlineKeyboard back to start menu or the option to remove more
    keyboard = [[InlineKeyboardButton("remove more", callback_data=str(THREE))],
                [InlineKeyboardButton("back to menu", callback_data=str(ONE))]]
    # change last message send by bot
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=message,
                          reply_markup=InlineKeyboardMarkup(keyboard))
    # notify ConversationHandler of SEVENTH stage
    return SEVENTH


def show_cart(update, context):
    """edit message text to user cart"""
    bot = context.bot
    query = update.callback_query

    chat_id = update.effective_chat.id
    user = update.effective_user

    # all items ordered by user in message and his price to pay for them
    message_and_price = str_user_cart(chat_id, user.id)
    # InlineKeyboard back to start menu
    keyboard = [[InlineKeyboardButton("back to menu", callback_data=str(ONE))]]
    # change last message send by bot
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=message_and_price['message'],
                          reply_markup=InlineKeyboardMarkup(keyboard))
    # notify ConversationHandler of SEVENTH stage
    return SEVENTH


def str_user_cart(chat_id, user_id):
    """user order to string

    returns dictionary containing a message string with all products ordered from user or
    notification that the user ordered nothing, the dictionary also contains as price float

    :param chat_id: unique id of chat the message came from
    :type chat_id: str
    :param user_id: unique id of user the message came from
    :type user_id: str

    :return: items and full price of user card
    :rtype: dictionary with message and price"""
    price_cart = 0.0
    message = ""

    # checks if chat_id exists as key
    if chat_id in cart.keys():
        # checks if user_id exists as key
        if user_id in cart[chat_id].keys():
            cart_from_user = cart[chat_id][user_id]
            # iterating over all categories the user ordered from
            for category_id in cart_from_user.keys():
                # iterating over all products the user ordered
                for product_id in cart_from_user[category_id].keys():
                    amount = cart_from_user[category_id][product_id]
                    name = menu[category_id]['products'][product_id]['name']
                    price = float(menu[category_id]['products'][product_id]['price'].replace(' €', ''))
                    # adds price to full price the user needs to pay
                    price_cart += price * amount
                    # adding new row with all information the user need for his ordered product
                    message = message + str(amount) + "x " + name + " " + str(f'{price:.2f}') + " €" + "\n"
            # full price the user needs to pay
            message = message + "Sum: " + str(f'{price_cart:.2f}') + " €\n"
            return {'message': message, 'price': price_cart}
    message = "no items in cart\n"
    return {'message': message, 'price': price_cart}


def str_group_cart(chat_id: str):
    """group order to string

    :param chat_id: unique id of chat the message came from
    :type chat_id: str

    :return: group order or message when no orders where made
    :rtype: str"""
    message = ''
    chat_sum = 0.0
    # check if any orders where made
    if chat_id in cart.keys():
        # iterates over every card of user in that chat and adds it to message
        for user_id in cart[chat_id].keys():
            user = all_user_data[user_id]
            message = message + str(user.username) + " aka " + str(user.first_name) + ":\n"
            message_and_price = str_user_cart(chat_id, user_id)
            chat_sum += message_and_price['price']
            message = message + message_and_price['message']
        # adds formatted chat_sum with precision of two
        message = message + "Chat Sum: " + str(f'{chat_sum:.2f}') + " €"
    else:
        message = "No orders made in this group chat!"

    return message


def show_group_cart(update, context):
    """edit last message in chat to the group chat cart"""
    bot = context.bot
    query = update.callback_query
    chat_id = update.effective_chat.id
    # button for the option to go back to start menu
    keyboard = [[InlineKeyboardButton("back to menu", callback_data=str(ONE))]]
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=str_group_cart(chat_id),
                          reply_markup=InlineKeyboardMarkup(keyboard))
    # notify the ConversationHandler of SEVENTH stage
    return SEVENTH


def finish_question(update, context):
    """checks if orders where made and asks the user if he wants to finalize the order"""
    bot = context.bot
    query = update.callback_query
    chat_id = update.effective_chat.id
    # checks if any orders where made in that chat
    if chat_id in cart.keys():
        # question keyboard
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
    # notify the ConversationHandler the Conversation ended
    return ConversationHandler.END


def finish(update, context):
    """handles response of :func:`finish_question`"""
    bot = context.bot
    query = update.callback_query
    chat_id = update.effective_chat.id
    # replies group order and deletes all orders made in chat from cart
    if query.data == "yes":
        message = "Finalized your order. Pay and order at Izmir based on the following message:\n" + \
                  str_group_cart(chat_id)
        del cart[chat_id]
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=message)
        # notify the ConversationHandler that the Conversation ended
        return ConversationHandler.END
    # last message ist edited and nothing changed because the user decided otherwise
    if query.data == "no":
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text="No order made!")
        # notify the ConversationHandler that the Conversation ended
        return ConversationHandler.END
    # shows start menu
    if query.data == "menu":
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text="What do you want to do?",
                              reply_markup=get_start_menu())
        # back to FIRST stage
        return FIRST


def clear_all_question(update, context):
    """verification question

    Asks if the user really wants to delete all orders made in this chat"""
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
    """handles response of :func:`clear_all_question`"""
    bot = context.bot
    query = update.callback_query
    chat_id = update.effective_chat.id

    # deletes key chat_id of cart dictionary if user wants to delete all orders from chat
    if query.data == "yes":
        if chat_id in cart:
            del cart[chat_id]
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text="Deleted all orders for this chat!")
        # notify the ConversationHandler that the Conversation ended
        return ConversationHandler.END
    # last message ist edited and nothing deleted because the user decided otherwise
    if query.data == "no":
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text="Nothing changed!")
        # notify the ConversationHandler that the Conversation ended
        return ConversationHandler.END
    # shows start menu
    if query.data == "menu":
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text="What do you want to do?",
                              reply_markup=get_start_menu())
        # back to FIRST stage
        return FIRST


def get_start_menu():
    """returns the start menu

    :return: start menu
    :rtype: InlineKeyboardMarkup"""
    keyboard = [[InlineKeyboardButton("add food to cart", callback_data=str(ONE))],
                [InlineKeyboardButton("remove food from cart", callback_data=str(TWO))],
                [InlineKeyboardButton("your cart", callback_data=str(THREE))],
                [InlineKeyboardButton("group cart", callback_data=str(FOUR))],
                [InlineKeyboardButton("send order for group", callback_data=str(FIVE))],
                [InlineKeyboardButton("clear all orders from chat", callback_data=str(SIX))]]

    return InlineKeyboardMarkup(keyboard)


def start_over(update, context):
    """The same as :func:`start` while editing the last message send from bot instead of replying"""
    bot = context.bot
    query = update.callback_query
    reply_markup = get_start_menu()
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text="What do you want to do?",
                          reply_markup=reply_markup)
    # back to FIRST stage
    return FIRST


def start(update, context):
    """Entry Point function replying the conversation menu"""
    # store user data
    put_in_all_user_data(update.effective_user)
    # getting the start menu InlineKeyboardMarkup
    reply_markup = get_start_menu()
    # reply with menu markup
    update.message.reply_text("What do you want to do?", reply_markup=reply_markup)
    # telling the ConversationHandler we are in the FIRST Stage
    return FIRST


def put_in_all_user_data(user: dict):
    """stores user dictionary under the user id as key in dictionary

    :param user: dictionary containing user information like first_name, username, id
    :type user: object
    """
    all_user_data[user.id] = user


def help(update, context):
    """replies with help message in chat"""
    update.message.reply_text("Use /start to order food at Izmir Kebab")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """main function

    loads the BOT_API_TOKEN from denenv, adds all handlers to the Updater and starts the bot"""
    # load dotenv as environment variable
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    # Create the Updater and pass it your bot's token.
    # getting bot api token from environment variable
    updater = Updater(os.environ.get("BOT_API_TOKEN"), use_context=True)

    # creating the ConversationHandler with entrypoints and multiple stages
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

    # adding handlers to the bot
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
