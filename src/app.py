import os
import sqlite3
from flask import Flask, request, Response, jsonify
import requests
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# ---------------------------------------------------------------
# ENV Load
# ---------------------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

REDMINE_URL = os.getenv("REDMINE_URL")
MM_SLASH_TOKEN = os.getenv("MM_SLASH_TOKEN", "")

# ---------------------------------------------------------------
# Fernet Key 준비
# ---------------------------------------------------------------
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    # FERNET_KEY = Fernet.generate_key().decode()
    # print("⚠️ FERNET_KEY generated! Store this in your .env:", FERNET_KEY)
    raise Exception("FERNET_SECRET_KEY is missing! Set it in .env")

fernet = Fernet(FERNET_KEY.encode())

# ---------------------------------------------------------------
# SQLite DB 준비
# ---------------------------------------------------------------
DB_DIR = './db'
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = f"{DB_DIR}/sqlite3.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_keys (
            username TEXT PRIMARY KEY,
            redmine_id TEXT,
            api_key TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


def save_user_login(username, redmine_id, raw_api_key):
    encrypted_api_key = fernet.encrypt(raw_api_key.encode()).decode()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_keys (username, redmine_id, api_key)
        VALUES (?,?,?)
        ON CONFLICT(username) DO UPDATE SET
            redmine_id=excluded.redmine_id,
            api_key=excluded.api_key
    """, (username, redmine_id, encrypted_api_key))
    conn.commit()
    conn.close()


def load_user_login(username):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT redmine_id, api_key FROM user_keys WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None, None

    decrypted_key = fernet.decrypt(row[1].encode()).decode()
    return row[0], decrypted_key


def delete_user_login(username):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM user_keys WHERE username=?", (username,))
    conn.commit()
    conn.close()


def text_response(text):
    return Response(text, mimetype="text/plain; charset=utf-8")


def help_message():
    return text_response(
        "📌 사용법:\n"
        "/redmine login <id> <api_key>    → Redmine 로그인\n"
        "/redmine logout                  → 로그아웃\n"
        "/redmine me                      → 내 계정 정보\n"
        "/redmine list [project]          → 이슈 목록\n"
        "/redmine issue <id>              → 이슈 상세조회\n"
        "/redmine close <id>              → 이슈 닫기\n"
        "/redmine create <project> <제목> → 이슈 생성\n"
        "/redmine projects                → 프로젝트 목록\n"
    )

# ---------------------------------------------------------------
# Slash Command
# ---------------------------------------------------------------
@app.post("/slash/redmine")
def slash_redmine():
    mm_token = request.form.get("token", "")
    mm_user = request.form.get("user_name", "")
    text = request.form.get("text", "").strip()

    if MM_SLASH_TOKEN and mm_token != MM_SLASH_TOKEN:
        return text_response("Invalid token")

    if not text:
        return help_message()

    parts = text.split(" ", 1)
    command = parts[0]

    # -----------------------------------------------------------
    # LOGIN
    # -----------------------------------------------------------
    if command == "login":
        if len(parts) == 1:
            return text_response("사용법: /redmine login <redmine_id> <api_key>")

        sub = parts[1].split(" ", 1)
        if len(sub) != 2:
            return text_response("사용법: /redmine login <redmine_id> <api_key>")

        redmine_id = sub[0]
        api_key = sub[1]

        # -----------------------------
        # 🔐 API KEY 유효성 검증
        # -----------------------------
        verify_res = requests.get(
            f"{REDMINE_URL}/users/current.json",
            params={"key": api_key}
        )

        if not verify_res.ok:
            return text_response("❌ 로그인 실패: API Key가 올바르지 않습니다.")

        # 로그인 성공이므로 DB 저장
        save_user_login(mm_user, redmine_id, api_key)
        return text_response(
            f"🔑 로그인 완료!\n"
            f"- Mattermost 사용자: {mm_user}\n"
            f"- Redmine ID: {redmine_id}"
        )


    # -----------------------------------------------------------
    # LOGOUT
    # -----------------------------------------------------------
    if command == "logout":
        redmine_id, user_key = load_user_login(mm_user)
        if not user_key:
            return text_response("❌ 저장된 로그인 정보 없음")

        delete_user_login(mm_user)
        return text_response("🔓 로그아웃 완료!")

    # -----------------------------------------------------------
    # 로그인 여부 확인
    # -----------------------------------------------------------
    redmine_id, user_key = load_user_login(mm_user)
    if not user_key:
        return text_response(
            "❌ 로그인 필요\n"
            "/redmine login <redmine_id> <api_key>"
        )

    # -----------------------------------------------------------
    # /redmine me — 사용자 정보
    # -----------------------------------------------------------
    if command == "me":
        url = f"{REDMINE_URL}/users/current.json"
        res = requests.get(url, params={"key": user_key})

        if not res.ok:
            return text_response("사용자 정보 조회 실패")

        user = res.json().get("user", {})
        txt = (
            f"👤 Redmine 사용자 정보\n"
            f"- ID: {user.get('id')}\n"
            f"- Login: {user.get('login')}\n"
            f"- Name: {user.get('firstname')} {user.get('lastname')}\n"
            f"- Email: {user.get('mail')}"
        )
        return text_response(txt)

    # -----------------------------------------------------------
    # LIST
    # -----------------------------------------------------------
    if command == "list":
        project = parts[1].strip() if len(parts) > 1 else None

        params = {"key": user_key, "include": "project"}
        if project:
            params["project_id"] = project

        res = requests.get(f"{REDMINE_URL}/issues.json", params=params)
        if not res.ok:
            return text_response("이슈 조회 실패")

        issues = res.json().get("issues", [])
        if not issues:
            return text_response("이슈가 없습니다.")

        lines = []
        for i in issues:
            proj = i.get("project", {}).get("identifier") or i.get("project", {}).get("name", "unknown")
            lines.append(f"- [{proj}] #{i['id']} {i['subject']}")

        return text_response("\n".join(lines))

    # -----------------------------------------------------------
    # ISSUE — 상세조회
    # -----------------------------------------------------------
    if command == "issue":
        if len(parts) == 1:
            return text_response("사용법: /redmine issue <id>")

        issue_id = parts[1].strip()

        url = f"{REDMINE_URL}/issues/{issue_id}.json"
        res = requests.get(url, params={"key": user_key})

        if not res.ok:
            return text_response("이슈 조회 실패")

        issue = res.json()["issue"]
        txt = (
            f"📝 이슈 상세 정보\n"
            f"- ID: {issue['id']}\n"
            f"- 프로젝트: {issue['project']['name']}\n"
            f"- 제목: {issue['subject']}\n"
            f"- 상태: {issue['status']['name']}\n"
            f"- 담당자: {issue.get('assigned_to', {}).get('name','-')}\n"
            f"- 설명: {issue.get('description','(없음)')}"
        )
        return text_response(txt)

    # -----------------------------------------------------------
    # CLOSE — 이슈 닫기
    # -----------------------------------------------------------
    if command == "close":
        if len(parts) == 1:
            return text_response("사용법: /redmine close <id>")

        issue_id = parts[1].strip()
        payload = {"issue": {"status_id": 5}}   # 5=Closed

        url = f"{REDMINE_URL}/issues/{issue_id}.json"
        res = requests.put(url, params={"key": user_key}, json=payload)

        if not res.ok:
            return text_response("이슈 상태 변경 실패")

        return text_response(f"✅ 이슈 #{issue_id} Closed!")

    # -----------------------------------------------------------
    # CREATE
    # -----------------------------------------------------------
    if command == "create":
        if len(parts) == 1:
            return text_response("사용법: /redmine create <project> <제목>")

        sub = parts[1].split(" ", 1)
        if len(sub) < 2:
            return text_response("프로젝트와 제목 모두 필요")

        project = sub[0]
        subject = sub[1]

        payload = {"issue": {"project_id": project, "subject": subject}}

        res = requests.post(
            f"{REDMINE_URL}/issues.json",
            params={"key": user_key},
            json=payload
        )
        if not res.ok:
            return text_response("이슈 생성 실패")

        return text_response(f"🆕 [{project}] 이슈 생성됨: {subject}")

    # -----------------------------------------------------------
    # PROJECTS
    # -----------------------------------------------------------
    if command == "projects":
        res = requests.get(f"{REDMINE_URL}/projects.json", params={"key": user_key})
        if not res.ok:
            return text_response("프로젝트 조회 실패")

        projects = res.json().get("projects", [])
        txt = "\n".join(f"- {p['identifier']} : {p['name']}" for p in projects)
        return text_response(txt)

    # -----------------------------------------------------------
    return help_message()

# ---------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------
@app.get("/health")
def health():
    return jsonify({"status": "ok"})

# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)