MAX_HISTORY_TURNS = 20  
# Each 'turn' = 1 user message + 1 assistant reply = 2 entries.
# So MAX_HISTORY_TURNS=20 keeps the last 20 exchanges in memory.
# Adjust this if you notice Ollama slowing down (too much context).

class ConversationHistory:
    def __init__(self, system_prompt: str):
        # system_prompt is always index 0 — it never gets trimmed.
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]

    def add_user(self, text: str):
        """Append a user message."""
        self.messages.append({"role": "user", "content": text})
        self._trim()  # Check length after every addition

    def add_assistant(self, text: str):
        """Append Fairy's reply."""
        self.messages.append({"role": "assistant", "content": text})

    def _trim(self):
        """
        If the history is too long, remove the oldest user+assistant pair.
        We keep messages[0] (the system prompt) untouched — it slices from index 1.
        """
        non_system = self.messages[1:]  # Everything except the system prompt
        max_entries = MAX_HISTORY_TURNS * 2  # *2 because each turn = 2 messages

        if len(non_system) > max_entries:
            # Remove the oldest 2 entries (1 full turn)
            self.messages = [self.messages[0]] + non_system[2:]

    def get(self) -> list[dict]:
        """Return the full message list, ready to send to Ollama."""
        return self.messages

    def reset(self):
        """Clear history but keep the system prompt."""
        self.messages = [self.messages[0]]