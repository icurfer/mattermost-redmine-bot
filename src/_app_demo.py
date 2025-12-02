import os
from flask import Flask, request, jsonify, Response
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # JSON 한글 깨짐 방지

REDMINE_URL = os.getenv("REDMINE_URL", "https://redmine.example.com")
API_KEY = os.getenv("REDMINE_API_KEY", "your_redmine_api_key")
MM_SLASH_TOKEN = os.getenv("MM_SLASH_TOKEN", "")  # Mattermost Slash Command token


# -------------------------------
# Health Check
# -------------------------------
@app.get("/health")
def health():
    status = {"flask": "ok"}

    try:
        res = requests.get(
            f"{REDMINE_URL}/issues.json",
            params={"key": API_KEY},
            timeout=3
        )
        status["redmine"] = "ok" if res.ok else f"error {res.status_code}"
    except Exception as e:
        status["redmine"] = f"error: {e}"

    return jsonify(status)


# -------------------------------
# Slash Command
# -------------------------------
@app.post("/slash/redmine")
def slash_redmine():

    # Token 검증
    mm_token = request.form.get("token", "")
    if MM_SLASH_TOKEN and mm_token != MM_SLASH_TOKEN:
        return Response("Invalid token", mimetype="text/plain; charset=utf-8", status=403)

    text = request.form.get("text", "").strip()
    if not text:
        return help_message()

    parts = text.split(" ", 1)
    command = parts[0]

    # -------------------------------
    # /redmine list (<project>)
    # -------------------------------
    if command == "list":
        project = parts[1].strip() if len(parts) > 1 else None

        params = {
            "key": API_KEY,
            "include": "project"   # project 정보 항상 포함
        }
        if project:
            params["project_id"] = project

        try:
            res = requests.get(f"{REDMINE_URL}/issues.json", params=params)
            if not res.ok:
                return text_response(f"Redmine 호출 실패: {res.status_code}")

            issues = res.json().get("issues", [])
            if not issues:
                return text_response("이슈가 없습니다.")

            lines = []
            for i in issues:
                # identifier → 없으면 name 사용 → 그것도 없으면 unknown
                proj = (
                    i.get("project", {}).get("identifier")
                    or i.get("project", {}).get("name")
                    or "unknown"
                )
                subject = i.get("subject", "(제목 없음)")
                issue_id = i.get("id", "?")
                lines.append(f"- [{proj}] #{issue_id} {subject}")

            return text_response("\n".join(lines))

        except Exception as e:
            return text_response(f"Redmine 호출 중 오류: {e}")

    # -------------------------------
    # /redmine create <project> <제목>
    # -------------------------------
    if command == "create":

        if len(parts) == 1:
            return text_response("사용법: /redmine create <project> <제목>")

        subparts = parts[1].split(" ", 1)

        if len(subparts) < 2:
            return text_response(
                "프로젝트와 제목을 모두 지정해야 합니다.\n\n"
                "사용법:\n"
                "/redmine create <project> <제목>\n"
                "예: /redmine create java-study 서버 점검 필요"
            )

        project = subparts[0].strip()
        subject = subparts[1].strip()

        if not subject:
            return text_response(
                "이슈 제목이 비어있습니다.\n사용법: /redmine create <project> <제목>"
            )

        payload = {
            "issue": {
                "project_id": project,
                "subject": subject
            }
        }

        try:
            res = requests.post(
                f"{REDMINE_URL}/issues.json",
                params={"key": API_KEY},
                json=payload,
            )

            if not res.ok:
                return text_response(
                    f"이슈 생성 실패: {res.status_code}\n{res.text}"
                )

            return text_response(f"[{project}] 이슈 생성완료: {subject}")

        except Exception as e:
            return text_response(f"이슈 생성 중 오류: {e}")

    # -------------------------------
    # /redmine projects
    # -------------------------------
    if command == "projects":
        try:
            res = requests.get(
                f"{REDMINE_URL}/projects.json",
                params={"key": API_KEY},
                timeout=3
            )
            if not res.ok:
                return text_response(f"프로젝트 조회 실패: {res.status_code}")

            projects = res.json().get("projects", [])
            if not projects:
                return text_response("프로젝트가 없습니다.")

            lines = []
            for p in projects:
                identifier = p.get("identifier") or p.get("name") or "unknown"
                name = p.get("name") or identifier
                lines.append(f"- {identifier} : {name}")

            return text_response("\n".join(lines))

        except Exception as e:
            return text_response(f"프로젝트 조회 오류: {e}")

    # -------------------------------
    # 기타 명령
    # -------------------------------
    return help_message()


# -------------------------------
# 공용 함수
# -------------------------------
def text_response(text):
    return Response(text, mimetype="text/plain; charset=utf-8")


def help_message():
    msg = (
        "사용법:\n"
        "/redmine list                     → 전체 이슈 목록\n"
        "/redmine list <project>           → 특정 프로젝트 이슈\n"
        "/redmine create <project> <제목>  → 특정 프로젝트에 이슈 생성\n"
        "/redmine projects                 → 프로젝트 목록\n"
    )
    return text_response(msg)


# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
