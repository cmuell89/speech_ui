# a good tutorial for the overall process is here:
# https://www.pragnakalp.com/dialogflow-fulfillment-webhook-tutorial/

from flask import Flask, request, jsonify
import os
from pymongo import MongoClient

app = Flask(__name__)

# example from https://stackoverflow.com/questions/9383450/how-can-i-detect-herokus-environment
USE_LOCAL = 'ON_HEROKU' not in os.environ


def connectToDatabase():
    if USE_LOCAL:
        client = MongoClient('localhost', 27017)
        return client['speech_db']
    else:
        client = MongoClient(os.environ.get("MONGO_URL"))
        return client['speech_db']


def initialize(db):
    shopping_list = []
    doc = {
        "freezerTemp": 0,
        "fridgeTemp": 40,
        "shoppingList": shopping_list
    }
    db['refrigerator'].insert_one(doc)
    print(db['refrigerator'].find_one())


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
    mongo_id = db['refrigerator'].find_one()['_id']
    db['refrigerator'].find_one_and_update({"_id": mongo_id},
                                           {"$set": {"freezerTemp": temp}})


def get_freezer_temp(db):
    return db['refrigerator'].find_one()['freezerTemp']


def set_fridge_temp(db, temp):
    mongo_id = db['refrigerator'].find_one()['_id']
    db['refrigerator'].find_one_and_update({"_id": mongo_id},
                                           {"$set": {"fridgeTemp": temp}})


def get_fridge_temp(db):
    return db['refrigerator'].find_one()['fridgeTemp']


def add_to_shopping_list(db, item):
    mongo_id = db['refrigerator'].find_one()['_id']
    shopping_list = db['refrigerator'].find_one()['shoppingList']
    shopping_list.append(item)
    db['refrigerator'].find_one_and_update({"_id": mongo_id},
                                           {"$set": {"shoppingList": shopping_list}})


def remove_from_shopping_list(db, item):
    mongo_id = db['refrigerator'].find_one()['_id']
    shopping_list = db['refrigerator'].find_one()['shoppingList']
    if item in shopping_list:
        shopping_list.remove(item)
    db['refrigerator'].find_one_and_update({"_id": mongo_id},
                                           {"$set": {"shoppingList": shopping_list}})


def get_shopping_list(db):
    return db['refrigerator'].find_one()['shoppingList']


def clear_shopping_list(db):
    mongo_id = db['refrigerator'].find_one()['_id']
    db['refrigerator'].find_one_and_update({"_id": mongo_id},
                                           {"$set": {"shoppingList": []}})

# @app.route("/")
# def root():
#     return """
#     <h1>Commands:</h1>
#     <ul>
#         <li>/status - report the status of each light</li>
#         <li>/get/{light} - return the light status</li>
#         <li>/set/{light} - set the light status to on or off</li>
#         <li>/reset - reset the database</li>
#         <li>/lastRequest - see JSON of the last webhook request (for debugging)</li>
#     </ul>
#     """


@app.route("/<component>/")
def web_temp(component):
    db = connectToDatabase()
    if component == "freezer":
        temp = get_freezer_temp(db)
        return "The freezer is set to {} degrees Fahrenheit".format(temp)
    elif component == "fridge":
        temp = get_fridge_temp(db)
        return "The fridge is set to {} degrees Fahrenheit".format(temp)


@app.route("/<component>/<temp>")
def web_set_temp(component, temp):
    temp = int(temp)
    db = connectToDatabase()
    if component == "freezer":
        if not valid_freezer_temp(temp):
            return "Invalid temperature for the freezer. It must be between -10 and 10"
        temp = set_freezer_temp(db, temp)
        return "The freezer is set to {} degrees Fahrenheit".format(temp)
    elif component == "fridge":
        if not valid_fridge_temp(temp):
            return "You gave an invalid temperature for the fridge. It must be between 32 and 43"
        temp = set_fridge_temp(db, temp)
        return "The fridge is set to {} degrees Fahrenheit".format(temp)


@app.route("/shopping_list/")
def web_shopping_list():
    db = connectToDatabase()
    return "Here is your shopping list: {}.".format(get_shopping_list(db))


@app.route("/shopping_list/clear")
def web_clear_shopping_list():
    db = connectToDatabase()
    clear_shopping_list(db)
    return "Your shopping list has been cleared."


@app.route("/shopping_list/<item>/add")
def web_shopping_list_add(item):
    db = connectToDatabase()
    add_to_shopping_list(db, item)
    return "The following item has been added to your shopping list: {}".format(
            item)


@app.route("/shopping_list/<item>/remove")
def web_shopping_list_remove(item):
    db = connectToDatabase()
    remove_from_shopping_list(db, item)
    return "The following item has been removed to your shopping list: {}".format(
            item)


@app.route("/help")
def get_help():

    helpString = ("Here's what I can do:"
                  "\tWhat is the temperature of the freezer?"
                  "\tSet the freezer temp to XX degrees"
                  "\tWhat is the temperature of the fridge?"
                  "\tSet the fridge temp to XX degrees"
                  "\tAdd 'milk' to my shopping list."
                  "\tRemove 'milk' from my shopping list."
                  "\tWhat do I need to buy at the store?"
                  "\tClear my shopping list."
                  )
    return helpString


@app.route("/reset")
def web_reset():
    db = connectToDatabase()
    initialize(db)
    return "reset"


# create a route for webhook
@app.route("/dialog", methods=["POST"])
def handleDialog():
    data = request.get_json()
    print(data)
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


# run the app
if __name__ == '__main__':
    db = connectToDatabase()
    initialize(db)
    app.run()
