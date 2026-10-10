import json
from datetime import datetime, timezone
from openai import OpenAI
from .agents import public_agents, find_agent

SYSTEM = """You are MARKHOR, the master agent coordinating a registry of 200 specialists. Route each user request to the best single agent, or the smallest useful set. You must not claim external actions occurred unless a configured tool actually performed them. You cannot access device files, send email, control smart devices, or create real alarms unless an integration is configured. Do not ask for or expose secrets. Return ONLY valid JSON with keys: agent_id (string 001-200), agent_name, category, intent (one of answer, reminder, plan, generate, automation, other), title (short task title), due_at (ISO-8601 datetime with timezone or null), needs_confirmation (boolean), response (a concise answer or next-step plan). If user requests a reminder and gives a clear future date/time, set intent=reminder and due_at. If date/time is ambiguous or missing, do not invent it; ask a concise clarification in response and set due_at=null. Do not schedule destructive, financial, or external actions without confirmation."""

def get_client():
    import os, streamlit as st
    key = os.getenv("OPENAI_API_KEY", "")
    try: key = key or str(st.secrets.get("OPENAI_API_KEY", ""))
    except Exception: pass
    return OpenAI(api_key=key) if key else None

def route_prompt(prompt, model="gpt-4o-mini", memory_text=""):
    client = get_client()
    if not client:
        return {"agent_id":"001", "agent_name":"Master Router", "category":"System Management & Intelligence", "intent":"other", "title":"Task request", "due_at":None, "needs_confirmation":False, "response":"OpenAI API key is not configured. Add OPENAI_API_KEY in Streamlit Secrets to enable Markhor's AI routing."}
    registry = [{"id": a["id"], "name": a["name"], "category": a["category"]} for a in public_agents()]
    messages = [{"role":"system", "content": SYSTEM + "\nAgent registry:\n" + json.dumps(registry, ensure_ascii=False) + ("\nUser-approved memory context:\n" + memory_text if memory_text else "")}, {"role":"user", "content":prompt}]
    result = client.chat.completions.create(model=model, messages=messages, temperature=0.2, response_format={"type":"json_object"})
    data = json.loads(result.choices[0].message.content or "{}")
    agent = find_agent(data.get("agent_id", "001")) or find_agent("001")
    data["agent_id"] = agent["id"]
    data["agent_name"] = agent["name"]
    data["category"] = agent["category"]
    data.setdefault("intent", "other"); data.setdefault("title", "Task request"); data.setdefault("due_at", None)
    data.setdefault("needs_confirmation", False); data.setdefault("response", "I have prepared a plan for this request.")
    return data
