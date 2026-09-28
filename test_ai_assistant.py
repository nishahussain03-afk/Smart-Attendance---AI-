import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN is missing from the .env file.")

client = InferenceClient(
    api_key=HF_TOKEN,
    provider="groq"
)

SYSTEM_PROMPT = """
You are SmartAttend AI, an AI assistant for a college attendance management system.

Help users understand SmartAttend, attendance rules, marking procedures, attendance percentages, present/absent/holiday status, and how the application works.

SmartAttend configuration:
Department: B.Sc Computer Science with AI
Year: 2nd Year
Shift: Shift 2
Minimum attendance requirement: 75%
Attendance marking window: 1:00 PM to 1:15 PM

Never invent attendance records, student information, dates, percentages, or rules.
Never reveal personal information that is not supplied as context.
If a requested database fact is unavailable in the supplied context, say so.
Keep answers concise, clear, and student-friendly.
"""

def ask_smartattend(message, conversation_history=None):
    if not message or not message.strip():
        return "Please enter a question."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        for item in conversation_history:
            if (
                isinstance(item, dict)
                and item.get("role") in ["user", "assistant"]
                and item.get("content")
            ):
                messages.append({
                    "role": item["role"],
                    "content": item["content"]
                })

    messages.append({"role": "user", "content": message.strip()})

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        max_tokens=500,
        temperature=0.4
    )

    answer = response.choices[0].message.content

    if not answer:
        return "Sorry, I could not generate a response."

    return answer.strip()
