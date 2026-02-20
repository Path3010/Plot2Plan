"""
Groq Chat Integration.

Provides conversational AI for floor plan design with structured data extraction.
Includes fallback rule-based chatbot when Groq is unavailable.
"""

import json
import re
from typing import Optional
from config import GROQ_API_KEY, GROQ_MODEL

# Groq client (lazy init)
_groq_client = None


def _get_groq_client():
    """Lazy initialization of Groq client."""
    global _groq_client
    if _groq_client is None and GROQ_API_KEY:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


SYSTEM_PROMPT = """You are an AI assistant specialized in residential floor plan design. \
Help the user describe their dream home. Ask clarifying questions about total area, \
number of rooms, special amenities, and any irregular boundary shapes. Be concise and friendly.

After gathering enough information, summarize the requirements in a structured JSON format:
{
  "total_area": <number in sq ft>,
  "rooms": [
    {"room_type": "<type>", "quantity": <int>, "desired_area": <optional number>}
  ],
  "ready_to_generate": true/false
}

Valid room types: master_bedroom, bedroom, bathroom, kitchen, living, dining, study, \
garage, hallway, balcony, pooja, store, other.

When the user says "generate", "create", "build", or similar, set ready_to_generate to true.

Always respond naturally in conversation first, then include the JSON block at the end \
wrapped in ```json ... ``` if you have extracted any structured data."""


def _extract_json_from_response(text: str) -> Optional[dict]:
    """Extract JSON data from the LLM response."""
    # Look for JSON code blocks
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find inline JSON
    json_match = re.search(r'\{[^{}]*"rooms"[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


async def chat_with_groq(message: str, history: list) -> dict:
    """
    Send a message to Groq API and get a response.

    Args:
        message: User's message.
        history: List of previous messages [{"role": "user"/"assistant", "content": "..."}].

    Returns:
        Dict with 'reply', 'extracted_data', 'should_generate'.
    """
    client = _get_groq_client()

    if client is None:
        # Fallback to rule-based chatbot
        return _fallback_chat(message, history)

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )

        reply = response.choices[0].message.content

        # Extract structured data
        extracted = _extract_json_from_response(reply)
        should_generate = False

        if extracted:
            should_generate = extracted.get("ready_to_generate", False)

        # Clean the reply (remove JSON block for display)
        clean_reply = re.sub(r'```json\s*.*?\s*```', '', reply, flags=re.DOTALL).strip()
        if not clean_reply:
            clean_reply = reply

        return {
            "reply": clean_reply,
            "extracted_data": extracted,
            "should_generate": should_generate,
        }

    except Exception as e:
        # Fallback on any Groq error
        return _fallback_chat(message, history)


# ---- Fallback Rule-Based Chatbot ----

_FALLBACK_STATES = {
    "greeting": {
        "keywords": [],
        "response": "Welcome! I'll help you design your floor plan. What's the total area of your plot (in sq ft)?",
        "next": "area",
    },
    "area": {
        "keywords": ["sq ft", "square feet", "sqft", "area"],
        "response": "Got it! How many bedrooms do you need?",
        "next": "bedrooms",
    },
    "bedrooms": {
        "keywords": ["bedroom", "bed", "room"],
        "response": "How many bathrooms?",
        "next": "bathrooms",
    },
    "bathrooms": {
        "keywords": ["bathroom", "bath", "toilet"],
        "response": "Do you need any special rooms? (study, pooja room, store room, garage)",
        "next": "special",
    },
    "special": {
        "keywords": ["study", "pooja", "store", "garage", "no", "none"],
        "response": "Great! Do you have a boundary sketch to upload? You can also type 'generate' to create the plan with a rectangular boundary.",
        "next": "generate",
    },
    "generate": {
        "keywords": ["generate", "create", "build", "yes", "make"],
        "response": "Generating your floor plan now!",
        "next": "done",
    },
}


def _extract_number(text: str) -> Optional[int]:
    """Extract the first number from text."""
    match = re.search(r'\d+', text)
    return int(match.group()) if match else None


def _fallback_chat(message: str, history: list) -> dict:
    """Simple rule-based fallback chatbot."""
    msg_lower = message.lower()
    extracted = None
    should_generate = False

    # Determine current state from history length
    turn = len([h for h in history if h.get("role") == "user"])

    if turn == 0:
        reply = _FALLBACK_STATES["greeting"]["response"]
    elif turn == 1:
        num = _extract_number(message)
        area = num if num else 1200
        reply = f"Got it, {area} sq ft! {_FALLBACK_STATES['area']['response']}"
        extracted = {"total_area": area, "rooms": [], "ready_to_generate": False}
    elif turn == 2:
        num = _extract_number(message)
        bedrooms = num if num else 2
        reply = f"{bedrooms} bedroom(s). {_FALLBACK_STATES['bedrooms']['response']}"
        extracted = {"rooms": [{"room_type": "bedroom", "quantity": bedrooms}], "ready_to_generate": False}
    elif turn == 3:
        num = _extract_number(message)
        bathrooms = num if num else 1
        reply = f"{bathrooms} bathroom(s). {_FALLBACK_STATES['bathrooms']['response']}"
        extracted = {"rooms": [{"room_type": "bathroom", "quantity": bathrooms}], "ready_to_generate": False}
    elif turn == 4:
        rooms = []
        if "study" in msg_lower:
            rooms.append({"room_type": "study", "quantity": 1})
        if "pooja" in msg_lower:
            rooms.append({"room_type": "pooja", "quantity": 1})
        if "store" in msg_lower:
            rooms.append({"room_type": "store", "quantity": 1})
        if "garage" in msg_lower:
            rooms.append({"room_type": "garage", "quantity": 1})
        reply = _FALLBACK_STATES["special"]["response"]
        if rooms:
            extracted = {"rooms": rooms, "ready_to_generate": False}
    else:
        if any(kw in msg_lower for kw in ["generate", "create", "build", "make", "yes"]):
            reply = "Generating your floor plan now!"
            should_generate = True
            extracted = {"ready_to_generate": True}
        else:
            reply = "Would you like me to generate the floor plan? Type 'generate' when ready."

    return {
        "reply": reply,
        "extracted_data": extracted,
        "should_generate": should_generate,
    }
