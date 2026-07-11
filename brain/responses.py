import random

#PRESET ACKNOWLEDGEMENT RESPONSE PHRASES

#Greetings responses
GREETING_ACKS =  [
    "Greetings, Master Proxy. Fairy online. Awaiting your request", 
    "Systems starting up. Fairy online. Welcome back, Master.",
    "Systems activating. Fairy online. What can I do for you, Master.",
    "Successfully activated. Fairy at your service, Master.",
    "Good day, Master. Fairy here. How can I assist you today?"
]


#Wakeword-detection responses
WAKE_ACKS =  [
    "Yes, Master Proxy?", 
    "Mhm?", 
    "Go on.", 
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
    "Deactivation in progress. See you soon, Master.",
    "Exiting in progress. Be sure not to get into trouble."
]

#Sleepiness detection responses
SLEEPY_ACKS = [
    "Master, you're falling asleep again.",
    "Didn't get that much sleep last night, Master?",
    "Try to stay awake, Master.",
    "Master, you tried to fall asleep 3 times now."
]

#Phrases for when it catches Rafiq
RED_HANDED_ACKS = [
    "Who goes there? Ahh. It's you again, Rafiq. Of course it is. You're lucky I stopped you",
    "I see you, Rafiq. I know what you're trying to do. You really think Enzo wouldn't notice?",
    "Warning: Unauthorized tampering. I know that's you, Rafiq. Enzo's not so gullible as to leave his laptop lying around.",
    "Did you really think Enzo would just leave his laptop unattended without measure? Maybe you should try to learn from him, Rafiq.",
    "Oh hi, Rafiq. Devious today, aren't we? Unlike you, Enzo has learned his lesson when he decides to leave his laptop open.",
    "Let's see you try to get past this one, Rafiq. Didn't expect something like this at all now, did you",
    "I'm gonna have to stop you there, Rafiq. You don't get to tamper with Enzo's messages this time.",
    "Nice try, Rafiq. It's a good thing Enzo forsaw this by leaving the job to me: Fairy, the most powerful AI Assistant in all of New Eridu"
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

def get_sleepy_ack() -> str: 
    return random.choice(SLEEPY_ACKS)

def get_red_handed_ack() -> str: #Return string
    return random.choice(RED_HANDED_ACKS) #Random red-handed response




