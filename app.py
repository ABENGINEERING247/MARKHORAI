import os, json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import or_
from markhor.db import session, User, Task, Memory, ChatMessage
from markhor.security import hash_password, verify_password, valid_username, valid_email
from markhor.agents import public_agents
from markhor.ai import route_prompt

st.set_page_config(page_title="MARKHOR AI", page_icon="🐐", layout="wide")

try:
    from_zone = ZoneInfo("Asia/Karachi")
except ZoneInfoNotFoundError:
    from_zone = timezone(timedelta(hours=5))

st.markdown("""<style>
.block-container{padding-top:1.4rem;max-width:1250px}.hero{padding:1.3rem 1.5rem;border-radius:18px;background:linear-gradient(120deg,#101c32,#263e5b);color:#fff;margin-bottom:1rem}.hero h1{margin:0;color:#f5c451}.hero p{margin:.35rem 0 0;color:#dce5f1}.small-muted{color:#8a93a4;font-size:.85rem}
</style><div class="hero"><h1>🐐 MARKHOR AI</h1><p>One Master Agent · 200 Specialists · One Centralized Workspace</p></div>""", unsafe_allow_html=True)

# --- settings ---
def secret(key, default=""):
    value = os.getenv(key, default)
    try: value = value or str(st.secrets.get(key, default))
    except Exception: pass
    return value

MODEL = secret("OPENAI_MODEL", "gpt-4o-mini")

if "user_id" not in st.session_state: st.session_state.user_id = None
if "username" not in st.session_state: st.session_state.username = None
if "chat_session" not in st.session_state: st.session_state.chat_session = []

# --- auth ---
def login_screen():
    st.subheader("Welcome to your private Markhor workspace")
    login_tab, register_tab = st.tabs(["Sign in", "Create account"])
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username or email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign in", use_container_width=True)
        if submit:
            db = session()
            try:
                user = db.query(User).filter(or_(User.username == username.strip(), User.email == username.strip().lower())).first()
                if user and verify_password(password, user.password_hash):
                    st.session_state.user_id = user.id; st.session_state.username = user.username; st.session_state.chat_session = []
                    st.rerun()
                st.error("Invalid username/email or password.")
            finally: db.close()
    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("Username (3–80 letters, numbers, . _ -)")
            email = st.text_input("Email address")
            pw1 = st.text_input("Password (at least 12 characters)", type="password")
            pw2 = st.text_input("Confirm password", type="password")
            register = st.form_submit_button("Create private account", use_container_width=True)
        if register:
            if not valid_username(new_username): st.error("Username format is not valid.")
            elif not valid_email(email): st.error("Enter a valid email address.")
            elif len(pw1) < 12: st.error("Use a password with at least 12 characters.")
            elif pw1 != pw2: st.error("Passwords do not match.")
            else:
                db = session()
                try:
                    if db.query(User).filter(or_(User.username == new_username, User.email == email.lower())).first():
                        st.error("That username or email is already registered.")
                    else:
                        user = User(username=new_username, email=email.lower(), password_hash=hash_password(pw1))
                        db.add(user); db.commit(); db.refresh(user)
                        st.session_state.user_id = user.id; st.session_state.username = user.username; st.session_state.chat_session = []
                        st.success("Account created."); st.rerun()
                except Exception:
                    db.rollback(); st.error("Could not create account. Please try another username/email.")
                finally: db.close()
    st.caption("Accounts and memories are private within this application. For public deployment, configure a persistent PostgreSQL database and protect the app with HTTPS.")

if not st.session_state.user_id:
    login_screen(); st.stop()

uid = st.session_state.user_id
with st.sidebar:
    st.markdown("### 🐐 MARKHOR")
    st.caption(f"Signed in as **{st.session_state.username}**")
    page = st.radio("Workspace", ["Master Chat", "200 Agents", "Tasks & Reminders", "Private Memory", "Task History", "Settings"], label_visibility="collapsed")
    if st.button("Sign out", use_container_width=True):
        st.session_state.user_id = None; st.session_state.username = None; st.session_state.chat_session = []; st.rerun()
    st.divider()
    st.caption(f"Model: `{MODEL}`")
    st.caption("API: " + ("Configured" if secret("OPENAI_API_KEY") else "Not configured"))

# In-app browser notification while page is open; persistent alerts require worker + ntfy topic.
if page in ("Master Chat", "Tasks & Reminders", "Settings"):
    with st.expander("Browser notifications", expanded=False):
        components.html("""<div style='font:14px sans-serif'><button id='enable' style='padding:8px 12px;border-radius:8px;border:1px solid #999;cursor:pointer'>Enable browser notifications</button><span id='status' style='margin-left:10px'></span><script>
        const b=document.getElementById('enable'),s=document.getElementById('status');
        if(!('Notification' in window)){s.textContent='This browser does not support notifications.';b.disabled=true;}
        else {s.textContent='Permission: '+Notification.permission;b.onclick=async()=>{const p=await Notification.requestPermission();s.textContent='Permission: '+p;if(p==='granted')new Notification('MARKHOR AI',{body:'Browser notifications enabled while this page is active.'});};}
        </script></div>""", height=65)

if page == "Master Chat":
    st.subheader("Talk to Markhor")
    st.write("Describe a task naturally. Markhor chooses a specialist and returns a plan or answer. Reminders are saved when a clear due date/time is provided.")
    db = session()
    try:
        history = db.query(ChatMessage).filter(ChatMessage.user_id == uid).order_by(ChatMessage.id.desc()).limit(30).all()[::-1]
    finally: db.close()
    for m in history:
        with st.chat_message(m.role): st.markdown(m.content)
    prompt = st.chat_input("Ask Markhor to plan, create, analyze, remind, or coordinate…")
    if prompt:
        db = session()
        try:
            memories = db.query(Memory).filter(Memory.user_id == uid).order_by(Memory.id.desc()).limit(8).all()
            memory_text = "\n".join("- " + m.content for m in memories)
            db.add(ChatMessage(user_id=uid, role="user", content=prompt, agent_id="001")); db.commit()
        finally: db.close()
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Markhor is routing your request…"):
                try:
                    result = route_prompt(prompt, MODEL, memory_text)
                    answer = result.get("response", "I have prepared a plan.")
                    agent = result.get("agent_name", "Master Router")
                    due_text = result.get("due_at")
                    if result.get("intent") == "reminder" and due_text:
                        try:
                            parsed = datetime.fromisoformat(due_text.replace("Z", "+00:00"))
                            if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=from_zone)
                            due_utc = parsed.astimezone(timezone.utc).replace(tzinfo=None)
                            if due_utc <= datetime.now(timezone.utc).replace(tzinfo=None):
                                answer += "\n\nI did not save this reminder because its due time is not in the future. Please provide a future time."
                            else:
                                db = session()
                                try:
                                    task = Task(user_id=uid, title=(result.get("title") or "Reminder")[:300], details=prompt, agent_id=result.get("agent_id", "001"), due_at=due_utc, status="scheduled")
                                    db.add(task); db.commit(); db.refresh(task)
                                finally: db.close()
                                answer += f"\n\n**Reminder saved** for {parsed.astimezone(from_zone).strftime('%Y-%m-%d %I:%M %p %Z')} (task #{task.id}). Delivery requires the background worker and a configured notification channel."
                        except (ValueError, TypeError):
                            answer += "\n\nI could not parse that reminder time reliably. Please enter it in Tasks & Reminders."
                    shown = f"**Assigned specialist:** {agent} · Agent {result.get('agent_id','001')}\n\n{answer}"
                    st.markdown(shown)
                    db = session()
                    try: db.add(ChatMessage(user_id=uid, role="assistant", content=shown, agent_id=result.get("agent_id", "001"))); db.commit()
                    finally: db.close()
                except Exception as e:
                    st.error(f"Markhor could not complete this request: {e}")
    st.info("Markhor can reason and draft outputs through OpenAI. External actions such as sending email, modifying third-party systems, or controlling devices require explicit integrations.")

elif page == "200 Agents":
    st.subheader("Agent Directory · 200 specialists")
    agents = public_agents()
    cats = ["All categories"] + list(dict.fromkeys(a["category"] for a in agents))
    col1, col2 = st.columns([2,1])
    with col1: query = st.text_input("Search agents", placeholder="e.g. Python, reminder, research")
    with col2: category = st.selectbox("Category", cats)
    filtered = [a for a in agents if (category == "All categories" or a["category"] == category) and (query.lower() in (a["name"] + " " + a["description"] + " " + a["category"]).lower())]
    st.caption(f"Showing {len(filtered)} of 200 agents")
    for a in filtered:
        with st.container(border=True):
            c1,c2 = st.columns([3,1])
            with c1: st.markdown(f"**{a['id']} · {a['name']}**\n\n{a['description']}\n\n`{a['category']}`")
            with c2:
                if st.button("Ask Markhor", key="agent_"+a["id"]):
                    st.session_state.prefill = f"Use the {a['name']} agent to help me with: "
                    st.info("Open Master Chat and complete your prompt: " + st.session_state.prefill)

elif page == "Tasks & Reminders":
    st.subheader("Tasks & Reminders")
    st.write("Times are interpreted in the selected timezone. A persistent worker must be running for scheduled delivery.")
    with st.form("task_form"):
        title = st.text_input("Reminder title", placeholder="Prepare AI lecture")
        details = st.text_area("Details (optional)")
        due_date = st.date_input("Date", value=datetime.now(from_zone).date() + timedelta(days=1))
        due_time = st.time_input("Time", value=datetime.strptime("08:00", "%H:%M").time())
        timezone_name = st.text_input("Timezone", value="Asia/Karachi")
        submitted = st.form_submit_button("Save reminder", use_container_width=True)
    if submitted:
        try:
            tz = ZoneInfo(timezone_name)
            local_due = datetime.combine(due_date, due_time).replace(tzinfo=tz)
            utc_due = local_due.astimezone(timezone.utc).replace(tzinfo=None)
            if not title.strip(): st.error("Enter a reminder title.")
            elif utc_due <= datetime.now(timezone.utc).replace(tzinfo=None): st.error("Choose a future date and time.")
            else:
                db = session()
                try: db.add(Task(user_id=uid,title=title.strip(),details=details,agent_id="002",due_at=utc_due,status="scheduled")); db.commit()
                finally: db.close()
                st.success("Reminder saved."); st.rerun()
        except ZoneInfoNotFoundError: st.error("Unknown timezone. Try Asia/Karachi, UTC, Europe/London, or America/New_York.")
    db = session()
    try: tasks = db.query(Task).filter(Task.user_id == uid, Task.status.in_(["scheduled","due"])).order_by(Task.due_at).all()
    finally: db.close()
    st.markdown("### Upcoming / due")
    if not tasks: st.caption("No active reminders.")
    for task in tasks:
        local_dt = task.due_at.replace(tzinfo=timezone.utc).astimezone(from_zone)
        with st.container(border=True):
            c1,c2 = st.columns([4,1])
            with c1:
                st.markdown(f"**{task.title}** · `{task.status}`")
                st.caption(local_dt.strftime("%a, %d %b %Y · %I:%M %p %Z"))
                if task.details: st.write(task.details)
            with c2:
                if st.button("Complete", key=f"done_{task.id}"):
                    db=session()
                    try:
                        t=db.query(Task).filter(Task.id==task.id,Task.user_id==uid).first()
                        if t: t.status="completed"; db.commit()
                    finally: db.close()
                    st.rerun()
                if st.button("Delete", key=f"delete_{task.id}"):
                    db=session()
                    try:
                        t=db.query(Task).filter(Task.id==task.id,Task.user_id==uid).first()
                        if t: db.delete(t); db.commit()
                    finally: db.close()
                    st.rerun()

elif page == "Private Memory":
    st.subheader("Private Memory")
    st.caption("Only your own saved memory entries are shown to your Markhor sessions. Save only information you are comfortable storing.")
    with st.form("memory_form"):
        memory = st.text_area("Save a preference or useful context", placeholder="I prefer concise project reports…")
        save = st.form_submit_button("Save memory")
    if save and memory.strip():
        db=session()
        try: db.add(Memory(user_id=uid,content=memory.strip())); db.commit()
        finally: db.close()
        st.success("Memory saved."); st.rerun()
    db=session()
    try: memories=db.query(Memory).filter(Memory.user_id==uid).order_by(Memory.id.desc()).all()
    finally: db.close()
    if not memories: st.info("No saved memories yet.")
    for m in memories:
        with st.container(border=True):
            st.write(m.content)
            if st.button("Delete memory", key=f"mem_{m.id}"):
                db=session()
                try:
                    obj=db.query(Memory).filter(Memory.id==m.id,Memory.user_id==uid).first()
                    if obj: db.delete(obj); db.commit()
                finally: db.close()
                st.rerun()

elif page == "Task History":
    st.subheader("Task & Conversation History")
    db=session()
    try:
        tasks=db.query(Task).filter(Task.user_id==uid).order_by(Task.created_at.desc()).limit(200).all()
        messages=db.query(ChatMessage).filter(ChatMessage.user_id==uid).order_by(ChatMessage.created_at.desc()).limit(100).all()
    finally: db.close()
    st.markdown("### Tasks")
    if tasks:
        st.dataframe([{"ID":t.id,"Title":t.title,"Agent":t.agent_id,"Due (UTC)":str(t.due_at),"Status":t.status,"Created":str(t.created_at)} for t in tasks], use_container_width=True, hide_index=True)
    else: st.caption("No tasks recorded.")
    st.markdown("### Recent chat")
    for m in messages:
        with st.expander(f"{m.role.title()} · {m.created_at} · Agent {m.agent_id}"):
            st.write(m.content)
    if st.button("Export my history as JSON"):
        payload={"tasks":[{"id":t.id,"title":t.title,"details":t.details,"agent_id":t.agent_id,"due_at":str(t.due_at),"status":t.status} for t in tasks],"messages":[{"role":m.role,"content":m.content,"agent_id":m.agent_id,"created_at":str(m.created_at)} for m in messages]}
        st.download_button("Download JSON", json.dumps(payload,ensure_ascii=False,indent=2), file_name="markhor_history.json", mime="application/json")

elif page == "Settings":
    st.subheader("Settings & Integrations")
    st.markdown("### OpenAI")
    st.write("API key status:", "Configured" if secret("OPENAI_API_KEY") else "Missing")
    st.write("Configured model:", MODEL)
    st.caption("Set OPENAI_API_KEY and OPENAI_MODEL in Streamlit Community Cloud → App settings → Secrets. Never put keys in GitHub.")
    st.markdown("### Notifications")
    st.write("Browser notification permission is managed by the browser. For scheduled notifications when this app is closed, deploy `worker.py` on an always-on worker host and configure `NTFY_TOPIC`.")
    st.markdown("### Data & privacy")
    st.write("Database:", "PostgreSQL configured" if secret("DATABASE_URL") else "Local SQLite fallback (not recommended for multi-user cloud persistence)")
    st.warning("For a real multi-user deployment, configure managed PostgreSQL (e.g. Neon or Supabase) using DATABASE_URL. Streamlit Community Cloud can hibernate inactive apps; a separate worker is required for dependable scheduled delivery.")
    st.markdown("### Push setup (ntfy)")
    st.write("Install the ntfy app on supported phones or open the ntfy web app, subscribe to a private topic, and set NTFY_TOPIC on the worker. Treat the topic name as a secret. Anyone who knows a public topic may be able to read its messages.")
    st.markdown("### Sign-in security")
    st.write("Passwords are stored as salted PBKDF2 hashes. For public production use, add email verification, rate limiting, account recovery, and a managed identity provider or reverse-proxy access controls.")
