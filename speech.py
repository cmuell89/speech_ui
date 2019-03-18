# demo app for webhooks and python
# this app demonstrates a simple stateful web app 
# that can be controlled via webhooks
#
# this should be deployed at https://csci4849-demo.herokuapp.com
#
# it uses the following libraries:
# flask for parsing web requests: http://flask.pocoo.org
# redis for simple object storage: https://pypi.org/project/redis/
#
# this can be deployed for free using heroku. see example here:
# https://github.com/datademofun/heroku-basic-flask
#
# we use a simple redis database because heroku apps can't reliably
# retain their state. this uses the free heroku redis store
# from https://elements.heroku.com/addons/heroku-redis
#
# about this app: this app tracks the status of three lights in a house
# (kitchen, livingroom, bedroom). each can be turned on and off
# and the status can be read. in the current version, this just updates
# the database, but you should be able to connect this to real stuff
# without much work
#
# a good tutorial for the overall process is here:
# https://www.pragnakalp.com/dialogflow-fulfillment-webhook-tutorial/

from flask import Flask, request, jsonify
import os
from pymongo import MongoClient
import json


app = Flask(__name__)


# use local settings for connecting to the database
# example from https://stackoverflow.com/questions/9383450/how-can-i-detect-herokus-environment
USE_LOCAL = not 'ON_HEROKU' in os.environ



# connect to the database and return the db handle
def connectToDatabase():
  
    if USE_LOCAL:
        client = MongoClient('localhost', 27017)
        db = client['test-database']
    else:
        client = MongoClient('localhost', 27017)
        db = redis.from_url(os.environ.get("MONGO_URL"))

    # initialize if we need to
    return db

# intitialize the database. we only need to do this once
# we set all the lights to off      
# 
# note here that we are just using the light name as database variable names
# in a real app we would probably want to use some namespace prefix to keep
# everything from getting jammed up


def initialize(db):
    shoppingList = []
    db.set("shoppingList", json.dumps(shoppingList))
    db.set("freezerTemp", 0)
    db.set("fridgeTemp", 40)


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
    db.set('freezerTemp', temp)


def get_freezer_temp(db):
    return db.get("freezerTemp")


def set_fridge_temp(db, temp):
    db.set('fridgeTemp', temp)


def get_fridge_temp(db):
    return db.get("fridgeTemp")


def add_to_shopping_list(db, item):
    print(str(db.get('shoppingList')))
    print(type(db.get('shoppingList')))
    shopping_list = json.loads(str(db.get('shoppingList')))
    shopping_list.append(item)
    db.set('shoppingList', json.dumps(shopping_list))


def remove_from_shopping_list(db, item):
    shopping_list = json.loads(str(db.get('shoppingList')))
    if item in shopping_list:
        shopping_list.remove(item)
    db.set('shoppingList', json.dumps(shopping_list))


def get_shopping_list(db):
    return json.loads(str(db.get('shoppingList')))


def clear_shopping_list(db):
    shoppingList = []
    db.set("shoppingList", json.dumps(shoppingList))

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
def webFreezerTemp(light):
    db = connectToDatabase()
    temp = getFreezerTemp(db)
    return "The freezer is set to {} degrees Fahrenheit".format(temp)


@app.route("/<component>/<value>")
def webSetTemp(light, value):
    db = connectToDatabase()
    setLight(db, light, value)
    return "The " + light + " light is now " + value


# for readability's sake, here we represent the status as HTML
# below in the webhook section we represent it as a string
# to improve understandability of the text
# if textOnly is true, strip out the html

@app.route("/help")
def getHelp():

    # return status as a string (to work with dialogflow)
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
def webReset():
    db = connectToDatabase()
    initialize(db)
    return "ok"


# this is for debugging the webhook code
# it just prints out the json of the last webhook request
@app.route("/lastRequest")
def lastRequest():
    db = connectToDatabase()
    req = db.get("lastRequest")
    return req


# create a route for webhook
@app.route("/dialog", methods=["POST"])
def handleDialog():
    data = request.get_json()
    # save this request for debugging
    db = connectToDatabase()
    db.set("lastRequest", json.dumps(data))
    print(data)
    if data['queryResult']['intent']['displayName'] == "help":
        # Help Intent
        response = getHelp()
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "set_fridge_temp":
        # Set Fridge Temp Intent
        temp = data['queryResult']['parameters']['fridge_temp']
        if valid_fridge_temp(temp):
            set_fridge_temp(db, temp)
            response = "The refrigerator temperature was set to {} degrees Fahrenheit.".format(temp)
        else:
            response = "You gave an invalid temperature for the fridge. It must be between 32 and 43"
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "get_fridge_temp":
        # Get Fridge Temp Intent
        temp = get_fridge_temp(db)
        response = "The refrigerator temperature is {} degrees Fahrenheit.".format(temp)
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "set_freezer_temp":
        # Set Freezer Temp Intent
        temp = data['queryResult']['parameters']['freezer_temp']
        if valid_freezer_temp(temp):
            set_fridge_temp(db, temp)
            response = "The freezer temperature was set to {} degrees Fahrenheit.".format(temp)
        else:
            response = "You gave an invalid temperature for the fridge. It must be between -10 and 10"
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "get_freezer_temp":
        # Get Freezer Temp Intent
        temp = get_freezer_temp(db)
        response = "The freezer temperature is {} degrees Fahrenheit.".format(temp)
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "get_shopping_list":
        shopping_list = get_shopping_list(db)
        response = "Here is your shopping list: {}.".format(shopping_list)
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "get_shopping_list":
        clear_shopping_list(db)
        response = "Your shopping list has been cleared."
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "add_item_to_shopping_list":
        item = data['queryResult']['parameters']['shopping_item']
        add_to_shopping_list(db, item)
        response = "The following item has been added to your shopping list: {}".format(item)
        print(response)
        return jsonify({'fulfillmentText': response})
    elif data['queryResult']['intent']['displayName'] == "remove_item_from_shopping_list":
        item = data['queryResult']['parameters']['shopping_item']
        remove_from_shopping_list(db, item)
        response = "The following item has been removed to your shopping list: {}".format(item)
        print(response)
        return jsonify({'fulfillmentText': response})


# run the app
if __name__ == '__main__':
    db = connectToDatabase()
    initialize(db)
    app.run()