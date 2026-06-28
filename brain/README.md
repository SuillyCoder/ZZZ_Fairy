# Brain — Orchestration & Persona

This is Fairy's decision-making core: it figures out *what* you're asking for, *who* Fairy is when she answers, and *remembers* enough about the conversation to handle natural follow-ups like "yes" or "do it."

## Intent classification — `intent.py`

Every transcribed request gets routed to one of several intents (`weather`, `news`, `email`, `finance`, `code`, `discord`, `system`, `zzz`, `reset`, `exit`, or the `chat` fallback) before any module-specific logic runs.

- Uses a keyword registry (`INTENT_KEYWORDS`) with whole-word regex matching — fast, deterministic, no LLM call needed for routing
- Checks `SessionState` first, so a bare "yes" after Fairy asks a follow-up question resolves to the *previous* intent rather than falling through to generic chat
- Falls back to `chat` (handled by the LLM directly) when nothing matches

**Tools/libraries:** `re` (standard library only — no ML model in the loop here)

## Persona — `fairy_persona.py`

Defines `FAIRY_SYSTEM_PROMPT`, the system prompt that shapes every LLM response: sharp, witty, loyal, calls the user "Master" or "Master Proxy," speaks in short spoken-friendly sentences (no markdown, since responses get read aloud by the TTS pipeline). This is what gives Fairy her in-character voice as opposed to a generic assistant tone.

## Conversation memory — `conversation.py`

`ConversationHistory` keeps a rolling window of the last `N` exchanges (default 20 turns) to send as context to the LLM, so Fairy can hold a coherent multi-turn conversation without re-explaining herself every message.

- The system prompt always stays at index 0 and is never trimmed
- Old turns get dropped in full pairs (user + assistant) once the window fills, so context never gets cut mid-exchange
- `reset()` wipes history back to just the system prompt — this is what "Fairy, reset your memory" triggers

**Tools/libraries:** none beyond Python standard library — this is a custom lightweight context window manager

## Session follow-ups — `session_state.py`

Tracks what Fairy just asked about, so a short reply like "yeah, go ahead" or "no, don't" can be resolved without re-stating the whole request.

- `update()` records the last intent/topic and whether Fairy is currently expecting a yes/no
- `resolve_followup()` checks incoming text against affirming/declining word lists and returns the original intent (to proceed) or `"decline"` (to back out)

**Tools/libraries:** `time` (for staleness tracking)

## LLM client — `ollama_client.py`

Despite the filename, this currently wraps the **Groq** chat completions API (`llama-3.1-8b-instant`) — the "fast brain" used for conversation, persona, and any intent that doesn't need heavy number-crunching. Takes the full message history from `ConversationHistory` and returns Fairy's reply text.

**Tools/libraries:** `groq`

## Canned responses — `responses.py`

A bank of pre-written, randomly-selected acknowledgment phrases (`get_greet_ack`, `get_wake_ack`, `get_confirmation_ack`, etc.) for instant, low-latency responses to common moments — boot-up, wake word detected, confirmation, decline, shutdown — without needing an LLM round-trip for something as simple as "yes, on it."

**Tools/libraries:** `random` (standard library)

## Current scope

| Capability | Status |
|---|---|
| Keyword-based intent routing | ✅ |
| Multi-turn conversation memory | ✅ |
| Follow-up resolution ("yes"/"no" after a question) | ✅ |
| In-character persona via system prompt | ✅ |
| Canned low-latency acknowledgments | ✅ |
| LLM-based intent classification (replacing keyword matching) | 🔲 Not yet — current approach is fully rule-based |
