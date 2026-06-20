import random

#PRESET ACKNOWLEDGEMENT RESPONSE PHRASES

#Greetings responses
GREETING_ACKS =  [
    "Greetings, Master Proxy. Fairy online. Awaiting your request", 
    "Systems starting up. Fairy online. Welcome back, Master.",
    "Systems activating. Fairy online. What can I do for you, Master.",
    "Successfully activated. Fairy at your service, Master.",
    "Good day, Master. How can I assist you today?"
]


#Wakeword-detection responses
WAKE_ACKS =  [
    "Yes, Master Proxy?", 
    "Mhm?", "Go on.", 
    "I'm listening, Master.", 
    "What is it?", 
    "At your service, Master.", 
    "Yes?", 
    "Reporting in. What's up?"
]

#Negligible audio responses
EMPTY_INPUT_ACKS = [
    "Didn't catch that, Master.", 
    "Come again?", 
    "What was that?",
    "I heard nothing useful there.", 
    "Static. Try that again, Master.", 
    "Sorry, Master. I couldn't catch that",
    "Could you please repeat that, Master?",
    "Sorry, you were saying?"
]

#Confirmation responses
CONFIRMATION_ACKS = [
    "Done.", 
    "On it.", 
    "On it, Master.",
    "Consider it handled, Master.", 
    "Already done, Master.", 
    "Taken care of.", 
    "As you wish, Master.", 
    "Affirmative, Master.",
    "Affirmative.",
    "Understood.",
    "Copy that, Master."
]

#Negation responses
DECLINE_ACKS = [
    "Understood, Master.",
    "Alright then.",
    "No worries, Master.",
    "Fair enough.",
    "Noted.",
]

 
#Shutdown responses
SHUTDOWN_ACKS = [
    "Systems shutting down. Bye for now, Master.",
    "Going offline. Stay safe, Master.",
    "Powering down. Catch you later, Master Proxy.",
    "Shutting down now. Don't miss me too much.",
    "Deactivation in progress. See you soon, Master."
    "Exiting in progress. Be sure not to get into trouble."
]


#Functions to return random response choice based on current state

def get_greet_ack() -> str: #Return string
    return random.choice(GREETING_ACKS) #Random wake response

def get_wake_ack() -> str: #Return string
    return random.choice(WAKE_ACKS) #Random wake response

def get_empty_ack() -> str: #Return string
    return random.choice(EMPTY_INPUT_ACKS) #Random wake response

def get_confirmation_ack() -> str: #Return string
    return random.choice(CONFIRMATION_ACKS) #Random wake response

def get_shutdown_ack() -> str: #Return string
    return random.choice(SHUTDOWN_ACKS) #Random wake response

def get_decline_ack() -> str: #Return string
    return random.choice(DECLINE_ACKS) #Random wake response



