# app.py
import os
import sqlite3
from flask import Flask, request, render_template, redirect, url_for
from functools import wraps
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__, template_folder="templates")

# -------------------------
# App State
# -------------------------
memory = []
test_fragments = []
solution_cache = []
rules_text = ""
need_rules = False
test_made = False

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
def query_openai_chat(messages, model="gpt-4o-mini", max_tokens=1024, temperature=0.2):
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content

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
        {"role": "system", "content": "You are a classifier that answers with exactly one word."},
        {"role": "user", "content": prompt}
    ]
    try:
        out = query_openai_chat(messages, model="gpt-4o-mini", temperature=0.0)
        return out.strip().lower().split()[0]
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

    rule_intro = f"Follow these rules: {rules}\n" if rules else ""

    prompt = (
        rule_intro
        + "Create a test in LATVIAN using the database information below. "
        + "Do NOT copy example questions; create original ones.\n\n"
        "DATABASE:\n"
        + db_text
    )

    messages = [
        {"role": "system", "content": "You create educational Latvian math tests."},
        {"role": "user", "content": prompt}
    ]

    response = query_openai_chat(messages)
    test_fragments.append(response)
    return response

# -------------------------
# Solve test
# -------------------------
def solve_test_fragments():
    if not test_fragments:
        return "Nav izveidots tests."
    combined = "\n\n".join(test_fragments)
    prompt = "Solve this test clearly:\n\n" + combined
    messages = [
        {"role": "system", "content": "You solve tests accurately."},
        {"role": "user", "content": prompt}
    ]
    out = query_openai_chat(messages)
    solution_cache.append(out)
    return out

# -------------------------
# Inquiry about test
# -------------------------
def answer_inquiry_about_test(question: str):
    context = "\n\n".join(test_fragments)
    prompt = f"Test context:\n{context}\n\nUser asks: {question}"
    messages = [
        {"role": "system", "content": "You answer questions about the test."},
        {"role": "user", "content": prompt}
    ]
    return query_openai_chat(messages)

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index1.html")

@app.errorhandler(500)
def internal_err(e):
    global need_rules, rules_text, test_made
    need_rules = False
    rules_text = ""
    test_made = False
    return redirect(url_for("index")), 500

@app.route("/", methods=["POST"])
def handle_post():
    global need_rules, rules_text, test_made, test_fragments, solution_cache

    user_input = request.form.get("request", "").strip()
    if not user_input:
        return render_template("index1.html", answer="Ieraksti tekstu.")

    memory.append("USER: " + user_input)
    classification = classify_question(user_input)

    # -------- PHASE 2: test exists --------
    if test_made:
        if classification == "inquiry":
            ans = answer_inquiry_about_test(user_input)
            return render_template("index1.html", answer=ans)

        if classification == "solution":
            ans = solve_test_fragments()
            return render_template("index1.html", answer=ans)

        if classification == "general":
            ans = query_openai_chat([
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ])
            return render_template("index1.html", answer=ans)

        if classification == "test":
            test_fragments = []
            solution_cache = []
            need_rules = True
            test_made = False
            return render_template("index1.html", answer="Ievadi testu veidošanas kritērijus.")

    # -------- PHASE 1: no test yet --------
    if classification == "test":
        need_rules = True
        return render_template("index1.html", answer="Ievadi testu veidošanas kritērijus ('nav', ja nav).")

    if need_rules:
        if user_input.lower() == "nav":
            result = make_test_from_db(None)
        else:
            result = make_test_from_db(user_input)

        need_rules = False
        test_made = True
        return render_template("index1.html", answer=result)

    if classification == "inquiry":
        db_preview = read_db_all("mathdb2.db")
        ans = query_openai_chat([
            {"role": "system", "content": "You answer database-related questions."},
            {"role": "user", "content": f"User asks: {user_input}\nDB:\n{str(db_preview)[:1500]}"}
        ])
        return render_template("index1.html", answer=ans)

    # general chat fallback
    ans = query_openai_chat([
        {"role": "system", "content": "You are a helpful assistant."},
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
