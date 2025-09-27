import os
import re
import json
import logging
import requests
import mysql.connector
import sqlparse
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from google.genai import Client
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "uniquery")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")

ALLOWED_TABLES = {
    "universities": ["id", "name", "location", "founded_year", "ranking"],
    "faculties": ["id", "name", "email", "title", "university_id"],
    "departments": ["id", "name", "university_id", "head_id"],
    "research_projects": ["id", "title", "department_id", "start_year", "end_year", "funding"]
}

DISALLOWED_TOKENS = [
    r"insert\b", r"update\b", r"delete\b", r"drop\b", r"alter\b",
    r"truncate\b", r"create\b", r"grant\b", r"revoke\b", r"shutdown\b",
    r"exec\b", r"system_user\b", r"into\b", r"load_file\b", r"outfile\b", r"--", r"/\*"
]

logging.basicConfig(filename="agent_chatbot.log", level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

client = Client(api_key=GEMINI_API_KEY)

def get_db_connection():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
    conn.database = MYSQL_DB
    return conn

def call_gemini(prompt: str, model="gemini-2.5-flash"):
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return (response.text or "").strip()
    except Exception as e:
        logging.error("Gemini API call failed: %s", e)
        return ""

def extract_first_select(text: str) -> str:
    m = re.search(r"(select\b.*?;)", text, flags=re.IGNORECASE | re.DOTALL)
    sql = m.group(1).strip() if m else text.strip()
    return sql.rstrip(";")

def is_sql_safe(sql: str):
    if not sql:
        return False, "Empty SQL"
    lowered = sql.lower()
    for tok in DISALLOWED_TOKENS:
        if re.search(tok, lowered):
            return False, f"Disallowed token detected: {tok}"
    try:
        parsed = sqlparse.parse(sql)
        if len(parsed) != 1:
            return False, "Multiple statements detected"
        if "select" not in parsed[0].normalized.lower().split()[0]:
            return False, "Only SELECT statements allowed"
    except Exception as e:
        return False, f"SQL parse error: {e}"
    tables = {t[1].lower() for t in re.findall(r"(?:from|join)\s+([`]?)(\w+)\1", sql, flags=re.IGNORECASE)}
    for table in tables:
        if table not in ALLOWED_TABLES:
            return False, f"Non-whitelisted table: {table}"
    return True, "OK"

def execute_select(sql: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(sql)
    cols = [c[0] for c in cur.description] if cur.description else []
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return cols, rows

def send_to_discord(message: str):
    if not DISCORD_WEBHOOK:
        return
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
    except Exception as e:
        logging.error("Discord webhook failed: %s", e)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_q = request.form.get("query", "").strip()
    if not user_q:
        flash("Please enter a question", "warning")
        return redirect(url_for("index"))

    logging.info("USER_QUERY: %s", user_q)

    try:
        table_columns_info = "\n".join([f"- {t}({', '.join(ALLOWED_TABLES[t])})" for t in ALLOWED_TABLES])
        sql_prompt = f"""Convert this user question into ONE safe MySQL SELECT query.
Only use these tables and columns:
{table_columns_info}

Return only SQL (no explanation).

Question: {user_q}
"""
        llm_sql_raw = call_gemini(sql_prompt)
        sql_query = extract_first_select(llm_sql_raw)

        ok, reason = is_sql_safe(sql_query)
        if not ok:
            return render_template("result.html", user_query=user_q, error=f"SQL validation failed: {reason}", llm_output=llm_sql_raw)

        cols, rows = execute_select(sql_query)

        table_preview = {"columns": cols, "rows": rows[:10], "total": len(rows)}
        format_prompt = f"""Summarize results for: {user_q}
SQL Results: {json.dumps(table_preview, default=str)}

Respond with:
1) A short natural-language summary.
2) Top 5 rows as Markdown table if rows exist.
"""
        formatted = call_gemini(format_prompt)

        return render_template("result.html", user_query=user_q, llm_output=sql_query,
                               columns=cols, rows=rows, formatted=formatted)

    except Exception as e:
        logging.exception("Error processing query")
        return render_template("result.html", user_query=user_q, error=str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
