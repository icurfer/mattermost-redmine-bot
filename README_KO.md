# mattermost-redmine-bot

`mattermost-redmine-bot`은 Mattermost에서 Redmine을 Slash Command로 연동하기 위한 유틸리티입니다.  
사용자는 Mattermost에서 직접 Redmine 이슈를 생성, 조회, 관리할 수 있으며, Redmine API를 통해 동작합니다.

---

## 📌 개요

이 프로젝트는 **Mattermost**와 **Redmine** 사이에 가벼운 명령 기반 인터페이스를 제공하여  
사용자가 채팅 환경을 벗어나지 않고 효율적으로 작업할 수 있도록 합니다.

백엔드는 **Flask**로 구현되었으며, 일부 기능은 **ChatGPT**의 도움을 받아 작성되었습니다.  
사용자 인증을 위해 SQLite 데이터베이스를 사용하여 Redmine 로그인 정보(Redmine ID + 암호화된 API Key)를 저장합니다.

---

## 🚀 주요 기능

- Mattermost Slash Command 연동  
- Mattermost 사용자별 Login/Logout 기능  
- Mattermost에서 직접 Redmine 이슈 생성  
- 이슈 목록 조회, 상세 조회, 상태 변경(닫기)  
- Redmine 프로젝트 목록 조회  
- **Fernet 암호화**를 이용한 API Key 보안 저장  
- 경량 **SQLite3** 데이터베이스 사용  
- Docker 테스트 완료 및 Kubernetes 배포 지원  
- 샘플 배포 템플릿 제공  

---

## 🛠 기술 스택

| 구성 요소 | 버전 / 설명 |
|----------|-------------|
| **Backend** | Flask (Python) |
| **Redmine** | 6.1.0 |
| **Mattermost** | Team Edition 10.7.2 |
| **Database** | SQLite3 (Redmine ID & API Key 암호화 저장) |
| **Deployment** | Docker → Kubernetes |

---

## 📚 동작 방식

1. Mattermost Slash Command가 Flask 백엔드로 요청을 보냄  
2. 백엔드는 Slash Token을 검증함  
3. 사용자는 Redmine ID와 API Key를 통해 로그인  
4. API Key는 Fernet으로 암호화되어 SQLite에 저장됨  
5. `list`, `create`, `issue`, `close`, `me`, `projects` 등 명령을 처리하여 Redmine API로 전달  
6. 결과는 Mattermost로 텍스트 포맷으로 응답됨  

---

## 🐳 배포 정보

이 프로젝트는 먼저 **Docker** 환경에서 테스트되었으며,  
이후 **Kubernetes** 환경으로 배포가 진행되었습니다.

README에는 빠른 배포를 위한 Deployment 및 Service 샘플 템플릿이 포함되어 있습니다.

---

## 💬 지원되는 Slash Command
```
/redmine login <id> <api_key>
/redmine logout
/redmine me
/redmine list [project]
/redmine issue <id>
/redmine close <id>
/redmine create <project> <subject>
/redmine projects
```


---

## 🔒 보안 안내

- `.env` 및 SQLite DB 파일은 Git에 **커밋하지 마세요.**  
- 다음 값은 반드시 안전하게 보호해야 합니다:
  - `FERNET_KEY`
  - `MM_SLASH_TOKEN`
  - Redmine API Key
- Kubernetes 환경에서는 환경변수를 **Secret**으로 관리하는 것을 권장합니다.

---

## 📦 포함된 템플릿

- Kubernetes Deployment (`deployment.yaml`)
- Kubernetes Service (`service.yaml`)
- `.env.example` 파일
- SQLite DB 자동 초기화
- Kubernetes용 `/health` 프로빙 엔드포인트

---

