#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import sys
import uuid
import re
import json
from collections import namedtuple
import urllib2
import requests
import json
import random


try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai


def create_user() :
 session_id = re.sub('[^A-Za-z0-9]+', '', str(uuid.uuid1()))
 print session_id
 return session_id


def get_contexts():
    url_contexts = "https://api.api.ai/v1/contexts?sessionId=%s"% sessionId
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization' : 'Bearer 71aeb35d73334779a10f6ce54ab9c881'}
    r = requests.get(url_contexts, headers=headers)
    contexts = json.loads(r.text)
    contexts_names = []
    print "contexts : ", contexts
    if contexts:
        for context_dict in contexts:
            contexts_names.append(context_dict['name'])
    return contexts_names

def get_json_values():
    with open('intent.json') as json_data:
        d = json.load(json_data)
        return d

def update_state(parameters, contextOut, flagUpdate):
    if currentState["contexts"] and flagUpdate == 1:
        for key in currentState["contexts"].keys():
            if currentState["contexts"][key]["lifespan"] == 0:
                del currentState["contexts"][key]
            else:
                currentState["contexts"][key]["lifespan"] -= 1
    for context in contextOut:
        currentState["contexts"][context] = {"lifespan" : 0}
    for p, v in parameters.iteritems():
        currentState["parameters"][p] = v


def get_response(user_says, contextOut, flagOut):
    if flagOut == 1:
        sysResponse, contextOut, parameters, flagOut, flagUpdate = get_response_apiai(user_says, contextOut)
    else:
        sysResponse, contextOut, parameters, flagOut, flagUpdate = get_response_custom_logic(user_says, contextOut)

    update_state(parameters, contextOut, flagUpdate)
    return sysResponse, contextOut, parameters, flagOut

def get_response_apiai(user_says, contextOut):
    # getting reponse from api.ai in json format
    request = ai.text_request()
    request.session_id = sessionId
    request.query = user_says
    response = request.getresponse()
    response_dict = json.loads(response.read().decode('utf-8'))

    # initialization/ default values
    parameters = {}
    contextOut = []
    flagOut = 1
    flagUpdate = 1

    # getting the name of the intent captured 
    intentName = response_dict["result"]["metadata"]["intentName"]

    if intentName != "Default Fallback Intent":
        # parameters = response_dict["result"]["parameters"]
        jump = intent_dict["intent"][intentName]["jump"]
        contextOut, flagOut = get_contextOut_flagOut(intentName, jump)
        contextIn = intent_dict["intent"][intentName]["contextIn"]

        # slot filling
        print "contexxxxtOut : ", contextOut
        print "parameters : ", parameters
        print "intentName : ", intentName
        # if "slotFilling" in intent_dict["intent"][intentName].keys(): 
        #     parameters = slot_filling(intentName, parameters)

        if not (set(contextOut).issubset(set(currentState["contexts"].keys()))) and set(contextIn).issubset(set(currentState["contexts"].keys())):
            parameters = response_dict["result"]["parameters"]
            print "parameters : ", parameters
            if "slotFilling" in intent_dict["intent"][intentName].keys(): 
                parameters = slot_filling(intentName, parameters)
            if intent_dict["intent"][intentName]["customResponse"] == "N":
                bot_says = random.choice(intent_dict["intent"][intentName]["sysResponse"])
            else:
                bot_says = get_custom_sysResponse(intentName)
        else:
            bot_says = "you already said that"
            flagUpdate = 0
    else:
        bot_says = random.choice(intent_dict["intent"]["Default Fallback Intent"]["sysResponse"])
        flagUpdate = 0

    return bot_says, contextOut, parameters, flagOut, flagUpdate

def get_response_custom_logic(user_says, contextOut):
    print currentState
    print "contextOut : ", contextOut

    for key in intent_dict["intent"].keys() :
        try:
            if intent_dict["intent"][key]["contextIn"] == contextOut:
                intentName = key
                break
        except:
            continue
    print "intentName : ", intentName

    parameters = {}
    contextOut = []
    flagOut = 0
    bot_says = ""
    jump = "Y"
    flagUpdate = 1

    if intentName == "query_field1_name_SSPR":
        jump = intent_dict["intent"][intentName]["jump"]
        contextOut, flagOut = get_contextOut_flagOut(intentName, jump)
        bot_says = get_custom_sysResponse(intentName)
        parameters = {"name" : user_says}
    elif intentName == "query_field2_studentId_SSPR":
        jump = intent_dict["intent"][intentName]["jump"]
        contextOut, flagOut = get_contextOut_flagOut(intentName, jump)
        bot_says = get_custom_sysResponse(intentName)
        parameters = {"studentId" : user_says}
    elif intentName == "query_field3_emailId_SSPR":
        jump = intent_dict["intent"][intentName]["jump"]
        contextOut, flagOut = get_contextOut_flagOut(intentName, jump)
        bot_says = get_custom_sysResponse(intentName)
        parameters = {"emailId" : user_says}

    print "contextOuuut : ", contextOut
    print "flagOuuut : ", flagOut
    print "intentNaaame : ", intentName
    return bot_says, contextOut, parameters, flagOut, flagUpdate


def get_contextOut_flagOut(intentName, jump):
    contextOut = []
    flagOut = 1
    if jump == "Y":
        if intentName == "error_message_1_pass_invalid":
            contextOut = intent_dict["intent"][verification_fields[0]["intentId"]]["contextIn"]
            if verification_fields[0] != verification_fields[-1]:
                flagOut = intent_dict["intent"][verification_fields[0]["intentId"]]["flagIn"]
        elif intentName == "query_field1_name_SSPR":
            contextOut = intent_dict["intent"][verification_fields[1]["intentId"]]["contextIn"]
            if verification_fields[1] != verification_fields[-1]:
                flagOut = intent_dict["intent"][verification_fields[1]["intentId"]]["flagIn"]
        elif intentName == "query_field2_studentId_SSPR":
            contextOut = intent_dict["intent"][verification_fields[2]["intentId"]]["contextIn"]
            # if verification_fields[2] != verification_fields[-1]:
            flagOut = intent_dict["intent"][verification_fields[2]["intentId"]]["flagIn"]
        elif intentName == "NO - problem_not_solved_SSPR":
            contextOut = intent_dict["intent"][authentication_fields[0]["intentId"]]["contextIn"]
            if authentication_fields[0] != authentication_fields[-1]:
                flagOut = intent_dict["intent"][authentication_fields[0]["intentId"]]["flagIn"]
        elif intentName == "error_message_2_acc_locked":
            contextOut = intent_dict["intent"][authentication_fields[0]["intentId"]]["contextIn"]
            if authentication_fields[0] != authentication_fields[-1]:
                flagOut = intent_dict["intent"][authentication_fields[0]["intentId"]]["flagIn"]
    else:
        contextOut = intent_dict["intent"][intentName]["contextOut"]
        flagOut = intent_dict["intent"][intentName]["flagOut"]
    return contextOut, flagOut


def get_custom_sysResponse(intentName):
    bot_says = ""
    if intentName == "error_message_1_pass_invalid":
        bot_says = random.choice(intent_dict["intent"][intentName]["sysResponse"]).replace("<field1>", verification_fields[0]["name"])
    elif intentName == "query_field1_name_SSPR":
        bot_says = random.choice(intent_dict["intent"][intentName]["sysResponse"]).replace("<field2>", verification_fields[1]["name"])
    elif intentName == "query_field2_studentId_SSPR":
        bot_says = random.choice(intent_dict["intent"][intentName]["sysResponse"]).replace("<field3>", verification_fields[2]["name"])
    elif intentName == "query_field3_emailId_SSPR":
        bot_says = random.choice(intent_dict["intent"][intentName]["sysResponse"]).replace("<link>", link)
    elif intentName == "NO - problem_not_solved_SSPR":
        bot_says = random.choice(intent_dict["intent"][intentName]["sysResponse"]).replace("<field1>", authentication_fields[0]["name"])
    elif intentName == "error_message_2_acc_locked":
        bot_says = random.choice(intent_dict["intent"][intentName]["sysResponse"]).replace("<field1>", authentication_fields[0]["name"])
    return bot_says

def get_verification_fields():
    verification_fields = []
    for field in intent_dict["verification_fields"]:
        if field["status"] == "Y":
            verification_fields.append({"intentId" : field["intentId"], "name" : field["name"]})
    print "verification_fields : ", verification_fields
    return verification_fields



def get_authentication_fields():
    authentication_fields = []
    for field in intent_dict["authentication_fields"]:
        if field["status"] == "Y":
            authentication_fields.append({"intentId" : field["intentId"], "name" : field["name"]})
    print "authentication_fields : ", authentication_fields
    return authentication_fields


def slot_filling(intentName, parameters):
    essentialSlots = intent_dict["intent"][intentName]["slotFilling"].keys()
    for slot in essentialSlots:
        while (not parameters[slot]):
            bot_says = intent_dict["intent"][intentName]["slotFilling"][slot]["sysResponse"]
            print "\nBot says : ", bot_says
            user_says = raw_input("\nUser says : ")
            parameters[slot] = user_says
    return parameters

if __name__ == "__main__":
    # Setting up API.AI
    CLIENT_ACCESS_TOKEN = '71aeb35d73334779a10f6ce54ab9c881'
    ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
    sessionId = create_user()
    currentState = {"contexts" : {}, "parameters" : {}}

    # Getting the name of the institution
    school = raw_input("Enter the name of the institution : ")

    # getting Intent dictionary 
    intent_dict = get_json_values()

    # default values/initializaion
    parameters = {}
    contextOut = []
    flagUpdate = 1
    link = "www.abcd.com"

    # state after default system response
    default_sysResponse = intent_dict["intent"]["Default start message"]["sysResponse"]
    sysResponse = default_sysResponse.replace("<school>", school)
    contextOut = intent_dict["intent"]["Default start message"]["contextOut"]
    update_state(parameters, contextOut, flagUpdate)

    print "\nBot says : ", sysResponse
    print "\ncontextOut : ", contextOut
    print "\ncurrentState : ", currentState

    # getting verification/authentication fields
    verification_fields = get_verification_fields()
    authentication_fields = get_authentication_fields()

    # <flagOut> to decide who is going to get the intent for the next user utterance (api.ai/ custom logic)
    flagOut = intent_dict["intent"]["Default start message"]["flagOut"]

    # conversation flow
    while("END_CHAT" not in contextOut):
        # recording user utterance
        user_says = raw_input("\nUser says : ")

        # getting response details
        sysResponse, contextOut, parameters, flagOut = get_response(user_says, contextOut, flagOut)

        print "\nBot says : ", sysResponse
        print "\ncontextOut : ", contextOut
        print " \ncurrentState : ", currentState







