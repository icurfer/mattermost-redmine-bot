# mattermost-redmine-bot

`mattermost-redmine-bot` is a Mattermost utility for integrating Slash Commands with Redmine.  
It enables users to create, view, and manage Redmine issues directly from Mattermost using the Redmine API.

---

## 📌 Overview

This project provides a lightweight command interface between **Mattermost** and **Redmine**, allowing teams to work efficiently without leaving the chat environment.

The backend is built with **Flask** and partially implemented using **ChatGPT**.  
For authentication and convenience, a small database is used to store Redmine login information (Redmine ID + encrypted API Key).

---

## 🚀 Features

- Mattermost Slash Command integration  
- Login/Logout feature for individual Mattermost users  
- Create Redmine issues directly from Mattermost  
- List, view, and close issues  
- Retrieve project list  
- Secure storage of API keys via **Fernet encryption**  
- Lightweight **SQLite3** database usage  
- Docker-tested and Kubernetes-ready  
- Includes sample deployment templates  

---

## 🛠 Technology Stack

| Component | Version / Description |
|----------|-------------|
| **Backend** | Flask (Python) |
| **Redmine** | 6.1.0 |
| **Mattermost** | Team Edition 10.7.2 |
| **Database** | SQLite3 (Redmine ID & API Key 암호화 저장) |
| **Deployment** | Docker → Kubernetes |

---

## 📚 How It Works

1. A Mattermost Slash Command sends a request to the Flask backend.  
2. The backend validates the Slash Command token.  
3. Users can log in by providing their Redmine ID and API key.  
4. API keys are encrypted with Fernet and stored in SQLite.  
5. Commands such as `list`, `create`, `issue`, `close`, `me`, and `projects`  
   are processed and forwarded to the Redmine API.  
6. Responses are returned to Mattermost in plain text format.

---

## 🐳 Deployment

This project was first tested on **Docker** and later deployed to **Kubernetes**.  
Sample Deployment and Service templates are included to help with quick deployment.

---

## 💬 Supported Slash Commands
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

## 🔒 Security Notes

- Do **NOT** commit `.env` or SQLite database files to Git.  
- Keep the following values secure and private:
  - `FERNET_KEY`
  - `MM_SLASH_TOKEN`
  - Redmine API keys
- For Kubernetes deployments, use **Secret** resources instead of plain text environment variables.

---

## 📦 Included Templates

- Kubernetes Deployment (`deployment.yaml`)
- Kubernetes Service (`service.yaml`)
- `.env.example`
- SQLite DB auto-initialization
- `/health` endpoint for Kubernetes probing


