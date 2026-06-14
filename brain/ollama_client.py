import requests, sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#Config imports
from config import FAIRY_GROQ_API_KEY, GROQ_MODEL
from groq import Groq

#Initialize Groq client
client = Groq(api_key=FAIRY_GROQ_API_KEY)

def chat(messages: list[dict]) -> str:
    try:
        completion = client.chat.completions.create(
                model=GROQ_MODEL,        # Which model to use
                messages=messages,       # Full conversation history — same format as Ollama
                max_tokens=150,          # Keep responses short since they're spoken aloud
                temperature=0.7,         # 0 = robotic/deterministic, 1 = creative/random
                                        # 0.7 is a good balance for a personality-driven assistant
            )

        response_text = completion.choices[0].message.content
            # Groq returns a standard OpenAI-compatible response object:
            # completion.choices = list of possible replies (we always want index 0)
            # .message.content = the actual text string

        print(f"[Groq]: {response_text}")  # So you can see it in terminal
        return response_text.strip()

    except Exception as e:
        print(f"[Groq Error]: {e}")
        return f"Sorry, I ran into an issue: {e}"