# a good tutorial for the overall process is here:
# https://www.pragnakalp.com/dialogflow-fulfillment-webhook-tutorial/

from flask import request, jsonify, Blueprint
import os
from pymongo import MongoClient

USE_LOCAL = True if 'ON_HEROKU' not in os.environ else False
if USE_LOCAL:
    DATABASE = 'refrigerator'
else:
    DATABASE = str(os.environ.get("DATABASE_NAME"))

webhook = Blueprint('webhook', __name__)


def connect_to_database():
    if USE_LOCAL:
        client = MongoClient('localhost', 27017)
        return client['speech_db']
    else:
        client = MongoClient(os.environ.get("MONGODB_URI"))
        return client[DATABASE]


def initialize(db):
    shopping_list = []
    doc = {
        "freezerTemp": 0,
        "fridgeTemp": 40,
        "shoppingList": shopping_list
    }
    db[DATABASE].insert_one(doc)


def valid_freezer_temp(temp):
    if temp > -10 and temp < 10:
        return True
    else:
        return False


def valid_fridge_temp(temp):
    if temp > 32 and temp < 43:
        return True
    else:
        return False


def set_freezer_temp(db, temp):
    mongo_id = db[DATABASE].find_one()['_id']
    db[DATABASE].find_one_and_update({"_id": mongo_id},
                                     {"$set": {"freezerTemp": temp}})


def get_freezer_temp(db):
    return db[DATABASE].find_one()['freezerTemp']


def set_fridge_temp(db, temp):
    mongo_id = db[DATABASE].find_one()['_id']
    db[DATABASE].find_one_and_update({"_id": mongo_id},
                                     {"$set": {"fridgeTemp": temp}})


def get_fridge_temp(db):
    return db[DATABASE].find_one()['fridgeTemp']


def add_to_shopping_list(db, item):
    mongo_id = db[DATABASE].find_one()['_id']
    shopping_list = db[DATABASE].find_one()['shoppingList']
    shopping_list.append(item)
    db[DATABASE].find_one_and_update({"_id": mongo_id},
                                     {"$set": {"shoppingList": shopping_list}})


def remove_from_shopping_list(db, item):
    mongo_id = db[DATABASE].find_one()['_id']
    shopping_list = db[DATABASE].find_one()['shoppingList']
    if item in shopping_list:
        shopping_list.remove(item)
    db[DATABASE].find_one_and_update({"_id": mongo_id},
                                     {"$set": {"shoppingList": shopping_list}})


def get_shopping_list(db):
    return db[DATABASE].find_one()['shoppingList']


def clear_shopping_list(db):
    mongo_id = db[DATABASE].find_one()['_id']
    db[DATABASE].find_one_and_update({"_id": mongo_id},
                                     {"$set": {"shoppingList": []}})


@webhook.route("/webhook/<component>/")
def web_temp(component):
    db = connect_to_database()
    if component == "freezer":
        temp = get_freezer_temp(db)
        return "The freezer is set to {} degrees Fahrenheit".format(temp)
    elif component == "fridge":
        temp = get_fridge_temp(db)
        return "The fridge is set to {} degrees Fahrenheit".format(temp)


@webhook.route("/webhook/<component>/<temp>")
def web_set_temp(component, temp):
    temp = int(temp)
    print(temp)
    db = connect_to_database()
    if component == "freezer":
        if not valid_freezer_temp(temp):
            return "Invalid temperature for the freezer. It must be between -10 and 10"
        set_freezer_temp(db, temp)
        return "The freezer has been set to {} degrees Fahrenheit".format(temp)
    elif component == "fridge":
        if not valid_fridge_temp(temp):
            return "You gave an invalid temperature for the fridge. It must be between 32 and 43"
        set_fridge_temp(db, temp)
        return "The fridge has been set to {} degrees Fahrenheit".format(temp)


@webhook.route("/webhook/shopping_list/")
def web_shopping_list():
    db = connect_to_database()
    return "Here is your shopping list: {}.".format(get_shopping_list(db))


@webhook.route("/webhook/shopping_list/clear")
def web_clear_shopping_list():
    db = connect_to_database()
    clear_shopping_list(db)
    return "Your shopping list has been cleared."


@webhook.route("/webhook/shopping_list/<item>/add")
def web_shopping_list_add(item):
    db = connect_to_database()
    add_to_shopping_list(db, item)
    return "The following item has been added to your shopping list: {}".format(
        item)


@webhook.route("/webhook/shopping_list/<item>/remove")
def web_shopping_list_remove(item):
    db = connect_to_database()
    remove_from_shopping_list(db, item)
    return "The following item has been removed to your shopping list: {}".format(
        item)


@webhook.route("/webhook/help")
def get_help():

    helpString = ("Here's what I can do:"
                  "\n\tWhat is the temperature of the freezer?"
                  "\n\tSet the freezer temp to XX degrees"
                  "\n\tWhat is the temperature of the fridge?"
                  "\n\tSet the fridge temp to XX degrees"
                  "\n\tAdd 'milk' to my shopping list."
                  "\n\tRemove 'milk' from my shopping list."
                  "\n\tWhat do I need to buy at the store?"
                  "\n\tClear my shopping list."
                  )
    return helpString


# create a route for webhook
@webhook.route("/webhook", methods=["POST"])
def handleDialog():
    data = request.get_json()
    if data['queryResult']['intent']['displayName'] == "help":
        # Help Intent
        response = get_help()
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "set_fridge_temp":
        # Set Fridge Temp Intent
        temp = data['queryResult']['parameters']['fridge_temp']
        response = web_set_temp('fridge', temp)
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "get_fridge_temp":
        # Get Fridge Temp Intent
        response = web_temp('fridge')
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "set_freezer_temp":
        # Set Freezer Temp Intent
        temp = data['queryResult']['parameters']['freezer_temp']
        response = web_set_temp('freezer', temp)
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "get_freezer_temp":
        # Get Freezer Temp Intent
        response = web_temp('freezer')
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "get_shopping_list":
        response = web_shopping_list()
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "clear_shopping_list":
        response = web_clear_shopping_list()
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "add_item_to_shopping_list":
        item = data['queryResult']['parameters']['shopping_item']
        response = web_shopping_list_add(item)
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "remove_item_from_shopping_list":
        item = data['queryResult']['parameters']['shopping_item']
        response = web_shopping_list_remove(item)
        print(response)
        return jsonify({'fulfillmentText': response})
