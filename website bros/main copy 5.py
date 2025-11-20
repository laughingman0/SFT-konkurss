# app.py
import os
import sqlite3
import html
import re
import secrets
from flask import Flask, request, render_template, redirect, url_for, session
from functools import wraps
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__, template_folder="templates")
app.secret_key = "teacherbro-super-secure-key-2024-" + secrets.token_hex(16)

# -------------------------
# Session-based state management
# -------------------------
def init_user_session():
    """Initialize session variables for a new user"""
    if 'test_fragments' not in session:
        session['test_fragments'] = []
    if 'solution_cache' not in session:
        session['solution_cache'] = []
    if 'need_rules' not in session:
        session['need_rules'] = False
    if 'test_made' not in session:
        session['test_made'] = False
    if 'rules_text' not in session:
        session['rules_text'] = ""

def get_user_test_fragments():
    return session.get('test_fragments', [])

def set_user_test_fragments(fragments):
    session['test_fragments'] = fragments

def get_user_solution_cache():
    return session.get('solution_cache', [])

def set_user_solution_cache(cache):
    session['solution_cache'] = cache

def get_user_need_rules():
    return session.get('need_rules', False)

def set_user_need_rules(value):
    session['need_rules'] = value

def get_user_test_made():
    return session.get('test_made', False)

def set_user_test_made(value):
    session['test_made'] = value

def get_user_rules_text():
    return session.get('rules_text', "")

def set_user_rules_text(value):
    session['rules_text'] = value

# -------------------------
# Simplified rules check
# -------------------------
def check_for_rules(message):
    """Simplified rules check - just detect if user explicitly says no rules"""
    message_lower = message.lower()
    
    # Check for explicit "no rules" phrases
    no_rules_phrases = [
        "no rules", "no criteria", "without rules", "any", "whatever",
        "doesn't matter", "doesnt matter", "no preference", "no specific",
        "surprise me", "you choose", "your choice", "anything"
    ]
    
    for phrase in no_rules_phrases:
        if phrase in message_lower:
            return "no rules"
    
    # If none of the above, assume user provided rules
    return "has rules"

# -------------------------
# DB
# -------------------------
def read_db_all(path="mathdb2.db"):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM topics;")
        rows = cur.fetchall()
        conn.close()
        return rows
    except sqlite3.OperationalError:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        if not tables:
            return []
        table = tables[0]
        cur.execute(f"PRAGMA table_info({table});")
        cols = [r[1] for r in cur.fetchall()]
        cur.execute(f"SELECT * FROM {table} LIMIT 100;")
        rows = cur.fetchall()
        conn.close()
        return {"table": table, "cols": cols, "rows": rows}

# -------------------------
# OpenAI helper (new API)
# -------------------------
def query_openai_chat(messages, model="gpt-4o-mini", max_tokens=2048, temperature=1):
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content

# ------------------------
# response cleaner for less fucking
# ----------------------------------

def clean_math_response(text: str) -> str:
    """Clean math responses and prepare for MathJax"""
    if not text:
        return ""
    
    # First, unescape HTML entities to handle them properly
    text = html.unescape(text)
    
    # Only remove actual LaTeX error messages, not mathematical content
    error_patterns = [
        r"^Misplaced &.*$",  # Only lines that START with "Misplaced &"
        r"^!.*$",  # Only lines that start with ! (LaTeX errors)
        r"LaTeX Error:.*$",
        r"Undefined control sequence.*$",
        r"MathJax processing.*$",
        r"TeX parse error.*$",
    ]
    
    for pattern in error_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Convert various LaTeX formats to MathJax format
    text = re.sub(r'\\\(', '$', text)
    text = re.sub(r'\\\)', '$', text)
    text = re.sub(r'\\\[', '$$', text)
    text = re.sub(r'\\\]', '$$', text)
    
    # Handle other LaTeX delimiters
    text = re.sub(r'\\begin\{equation\}(.*?)\\end\{equation\}', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{align\}(.*?)\\end\{align\}', r'$$\1$$', text, flags=re.DOTALL)
    
    # Protect math content - but DON'T escape &, <, > in math mode as they're valid
    def protect_math(match):
        math_content = match.group(1)
        # In math mode, these characters are valid, so leave them alone
        return f'${math_content}$'
    
    def protect_display_math(match):
        math_content = match.group(1)
        # In display math, these characters are valid
        return f'$${math_content}$$'
    
    # Process math content first
    text = re.sub(r'\$\$(.*?)\$\$', protect_display_math, text, flags=re.DOTALL)
    text = re.sub(r'\$(.*?)\$', protect_math, text, flags=re.DOTALL)
    
    # Now escape the non-math HTML content
    def escape_text(s: str):
        # Only escape real HTML characters
        s = s.replace("&", "&amp;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        return s

    parts = re.split(r'(\$.*?\$|\$\$.*?\$\$)', text, flags=re.DOTALL)
    processed_parts = []

    for part in parts:
        if part.startswith('$') and part.endswith('$'):
            processed_parts.append(part)
        else:
            processed_parts.append(escape_text(part))
        
        text = ''.join(processed_parts)
            
    # Fix common apostrophes and quotes in regular text
    text = re.sub(r"&#x27;", "'", text)
    text = re.sub(r"&quot;", '"', text)
    
    # Clean up multiple newlines and spaces
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

# -------------------------
# Classification
# -------------------------
def classify_question(user_question: str) -> str:
    prompt = (
        "Classify the following question as one word: either 'general', 'test', "
        "'inquiry', or 'solution'.\n\n"
        f"Question: '''{user_question}'''"
    )
    messages = [
        {"role": "system", "content": "You are a classifier that determines whether a student wants to converse generally with you, wants you to make a test, asks you to solve a test, or asks you a quesion regarding the test. Answer with exactly one word."},
        {"role": "user", "content": prompt}
    ]
    try:
        out = query_openai_chat(messages, model="gpt-4o-mini", temperature=0)
        classification = out.strip().lower().split()[0]
        print(f"Classified '{user_question}' as: {classification}")
        return classification
    except Exception:
        q = user_question.lower()
        if "test" in q or "izveido" in q:
            return "test"
        if "solve" in q or "atbildes" in q:
            return "solution"
        if "explain" in q or "kas ir" in q:
            return "inquiry"
        return "general"

# -------------------------
# Test creation
# -------------------------
def make_test_from_db(rules: str | None = None):
    db_content = read_db_all("mathdb2.db")

    db_text = ""
    if isinstance(db_content, dict):
        db_text += f"Table: {db_content['table']}\nColumns: {db_content['cols']}\n"
        for r in db_content["rows"]:
            db_text += repr(r) + "\n"
    else:
        for r in db_content[:200]:
            db_text += repr(r) + "\n"

    rule_intro = f"Follow these rules while making the test: {rules}\n" if rules else ""

    prompt = (
        rule_intro
        + "Create a test in English using the database information below. "
        + "Format your response using clean Markdown. "
        + "Use $...$ for inline math and $$...$$ for display math. "
        + "DO NOT use any other LaTeX commands. "
        + "DO NOT include any error messages or comments about LaTeX. "
        + "DO NOT use \\\\, \\#, \\&, \\% or other escaped characters in math mode. "
        + "only use the topics from the database WITHOUT using the examples mentioned in the database, such as the medieval archery problem."
        + "Come up with your own exercises and numbers."
        + "Keep it 100 king"
        + "Keep math expressions simple and compatible with MathJax. "
        + "Output only the test content, no explanations.\n\n"
        "DATABASE:\n"
        + db_text
    )

    messages = [
        {"role": "system", "content": "You are an educational AI called Synesis - you create math tests using ONLY $...$ for inline math and $$...$$ for display math. Never use other LaTeX commands or include error messages."},
        {"role": "user", "content": prompt}
    ]

    response = query_openai_chat(messages)
    
    # Store in user's session
    current_fragments = get_user_test_fragments()
    current_fragments.append(response)
    set_user_test_fragments(current_fragments)
    
    return response

# -------------------------
# Solve test
# -------------------------
def solve_test_fragments():
    test_fragments = get_user_test_fragments()
    if not test_fragments:
        return "Nav izveidots tests."
    combined = "\n\n".join(test_fragments)
    prompt = "Solve this test clearly. " + combined
    messages = [
        {"role": "system", "content": "You solve tests accurately.  When using LaTeX math, always use \\( ... \\) for inline math or $$...$$ for block math. Never escape backslashes. Output RAW LaTeX."},
        {"role": "system", "content": """Important:
            - NEVER include LaTeX compiler errors such as 
            "You can't use 'macro parameter character #' in math mode"
            or any messages describing TeX problems.
            - NEVER include debug comments, warnings, or explanations of LaTeX.
            - ONLY output clean, valid MathJax-compatible LaTeX using \( ... \) or $$ ... $$.
            - Do not escape backslashes.
            - Do not invent macros.
            - If unsure about formatting, simplify the expression rather than producing invalid LaTeX."""},
        {"role": "user", "content": prompt}
    ]
    out = query_openai_chat(messages)
    
    # Store in user's session
    current_cache = get_user_solution_cache()
    current_cache.append(out)
    set_user_solution_cache(current_cache)
    
    print(out)
    return out

# -------------------------
# Inquiry about test
# -------------------------
def answer_inquiry_about_test(question: str):
    test_fragments = get_user_test_fragments()
    context = "\n\n".join(test_fragments)
    prompt = f"Test context:\n{context}\n\nUser asks: {question}"
    messages = [
        {"role": "system", "content": "You are an educational AI named Synesis that answers questions about the test."},
        {"role": "user", "content": prompt}
    ]
    return query_openai_chat(messages)

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET"])
def index():
    init_user_session()  # Initialize session for this user
    return render_template("index1.html")

@app.errorhandler(500)
def internal_err(e):
    # Reset only this user's session
    init_user_session()
    return redirect(url_for("index")), 500

@app.route("/", methods=["POST"])
def handle_post():
    # Initialize user session at the start of each request
    init_user_session()
    
    user_input = request.form.get("request", "").strip()
    if not user_input:
        return render_template("index1.html")

    # Get current user's state from session
    need_rules = get_user_need_rules()
    test_made = get_user_test_made()
    
    classification = classify_question(user_input)
    print(f"DEBUG - Classification: '{classification}', need_rules: {need_rules}, test_made: {test_made}")

    # SIMPLIFIED LOGIC FLOW:
    
    # Case 1: User asks for a test for the first time
    if classification == "test" and not test_made and not need_rules:
        print("DEBUG - Starting new test creation")
        set_user_need_rules(True)
        set_user_test_made(False)
        set_user_test_fragments([])
        set_user_solution_cache([])
        return render_template("index1.html", answer="Is there any specific criteria for the test?")
    
    # Case 2: User is providing rules for a test
    elif need_rules:
        print(f"DEBUG - Processing rules input: '{user_input}'")
        rules_check = check_for_rules(user_input)
        print(f"DEBUG - Rules check result: '{rules_check}'")
        
        if rules_check == "no rules":
            print("DEBUG - Creating test without specific rules")
            result = make_test_from_db(None)
        else:
            print(f"DEBUG - Creating test with rules: '{user_input}'")
            result = make_test_from_db(user_input)

        set_user_need_rules(False)
        set_user_test_made(True)
        result = clean_math_response(result)
        from markdown import markdown
        html_result = markdown(result, extensions=['fenced_code', 'nl2br', "md_in_html"])
        from markupsafe import Markup
        return render_template("index1.html", answer=Markup(html_result))
    
    # Case 3: Test already exists, handle various requests
    elif test_made:
        if classification == "inquiry":
            ans = answer_inquiry_about_test(user_input)
            ans = clean_math_response(ans)
            from markdown import markdown
            html_answer = markdown(ans, extensions=['fenced_code', 'nl2br', "md_in_html"])
            from markupsafe import Markup
            return render_template("index1.html", answer=Markup(html_answer))

        elif classification == "solution":
            ans = solve_test_fragments()
            ans = clean_math_response(ans)
            from markdown import markdown
            html_answer = markdown(ans, extensions=['fenced_code', 'nl2br', "md_in_html"])
            from markupsafe import Markup
            return render_template("index1.html", answer=Markup(html_answer))

        elif classification == "test":
            # User wants a new test - reset this user's session
            print("DEBUG - Creating new test (replacing existing)")
            set_user_test_fragments([])
            set_user_solution_cache([])
            set_user_need_rules(True)
            set_user_test_made(False)
            return render_template("index1.html", answer="Is there any specific criteria for the test?")

        else:  # general or anything else
            ans = query_openai_chat([
                {"role": "system", "content": "You are an educational AI called Synesis - a helpful assistant."},
                {"role": "user", "content": user_input}
            ])
            ans = clean_math_response(ans)
            return render_template("index1.html", answer=ans)
    
    # Case 4: No test context, handle general requests
    else:
        if classification == "inquiry":
            db_preview = read_db_all("mathdb2.db")
            ans = query_openai_chat([
                {"role": "system", "content": "You answer database-related questions."},
                {"role": "user", "content": f"User asks: {user_input}\nDB:\n{str(db_preview)[:1500]}"}
            ])
            return render_template("index1.html", answer=ans)
        else:
            # general chat fallback
            ans = query_openai_chat([
                {"role": "system", "content": "You are an educational AI called Synesis - a helpful assistant."},
                {"role": "user", "content": user_input}
            ])
            return render_template("index1.html", answer=ans)

if __name__ == "__main__":
    if not os.path.exists("mathdb2.db") and os.path.exists("mathdb_new_new.sql"):
        conn = sqlite3.connect("mathdb2.db")
        with open("mathdb_new_new.sql", "r", encoding="cp1252", errors="replace") as f:
            conn.executescript(f.read())
        conn.close()

    app.run(host="0.0.0.0", port=5000, debug=True)