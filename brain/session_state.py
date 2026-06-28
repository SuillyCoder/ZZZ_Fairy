import time

class SessionState: #declare a single class instance of a session
    def __init__(self):
        #Declaring class variables
        self.last_intent = None #No prior intent set
        self.last_topic = None #No prior topic set
        self.awaiting_followup = False #Assuming Fairy's last response was not a question / follow up
        self.last_updated = time.time() #Timestamp for last updated session

    #State updating based on current state of session flags
    def update(self, intent:str, topic:str, expects_followup: bool = False):
        self.last_intent = intent
        if topic is not None: 
            self.last_topic = topic
        self.awaiting_followup = expects_followup
        self.last_updated = time.time()

    #Address followup based on the intent
    def resolve_followup(self, text: str) -> str | None:
        if not self.awaiting_followup or not self.last_intent: #If no followup to address
            return None #Simply do nothing
        text_lower = text.strip().lower() #Convert all to lowercase

        affirming_words = ["yes", "yeah", "yep", "sure", "please", "go ahead", "okay", "ok"] #Affirming words
        declining_words = ["no", "nah", "nope", "don't", "do not", "negative"] #Declining words
 
        #Classify directive either as affirmative or negative
        is_affirmative = any(word in text_lower for word in affirming_words)
        is_negative = any(word in text_lower for word in declining_words)

        if is_affirmative and not is_negative: #Affirming directive detected
            return self.last_intent #fulfill the intent
        if is_negative:
            return "decline" #Otherwise, don't 
        return None
    
    def reset(self): #Clears the state and resets everything
        self.last_intent = None
        self.last_topic = None
        self.awaiting_followup = False
        self.last_updated = time.time()




