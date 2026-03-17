# DreamBot

A Python-based Slack bot developed during my internship at Mavericks VFX to improve security and accessibility of internal company systems. DreamBot lets studio staff retrieve real-time information — render farm status, software license usage, project deliverables, and more — directly from Slack, without needing direct access to the internal network.

Built with the Slack Bolt framework and integrated with ShotGrid, Jira, and the Deadline render farm API.

---

## What it does

DreamBot exposes a set of slash commands that surface internal studio data in Slack. All sensitive credentials and server paths are managed through a constants file and never hardcoded.

| Command | Description |
|---|---|
| `/renders` | Shows all currently active render jobs on the farm |
| `/renderstatus [user or show]` | Shows render jobs for a specific user or show code |
| `/myrender` | Shows the render jobs submitted by the caller (resolved via their Slack email) |
| `/rollcall [department]` | Lists all active staff in a given department from ShotGrid |
| `/whohou` | Shows current Houdini license usage |
| `/whonuke` | Shows current Nuke license usage |
| `/whoasset [username]` | Returns all hardware assets checked out by a user |
| `/today` | Shows all final deliveries due today |
| `/due` | Shows all final deliveries due in the next week |
| `/studiotime [location]` | Shows the current time at any studio location (Toronto, Montreal, Stockholm, LA, Sydney) |
| `/mixtape` | Returns the latest Mixtape Monday Spotify link from the company inbox |
| `/links` | Displays internal company links |
| `/breach [message]` | Sends a security breach alert email (requires message longer than 4 characters) |
| `/911 [message]` | Sends an emergency alert email (requires message longer than 4 characters) |
| `/commands` | Lists all available commands with descriptions |
| `/workstation` | Shows the workstation assigned to the caller |

---

## How it works

**Slack integration** — built with [Slack Bolt for Python](https://slack.dev/bolt-python/) running in Socket Mode, which means the bot connects outbound to Slack over a WebSocket rather than requiring an inbound webhook endpoint. This was important for a studio environment where exposing internal servers to the public internet was not an option.

**ShotGrid** — the `backend.py` module connects to the studio's ShotGrid instance using the `shotgun_api3` library. It queries active projects, human users, departments, and task due dates to power the `/rollcall`, `/today`, `/due`, and related commands.

**Deadline render farm** — render status commands connect to the studio's Deadline render farm via `DeadlineConnect`, pulling active job data including job name, submitting user, progress, and running time.

**Email** — the `/mixtape` command pulls the most recent Mixtape Monday email from a Gmail inbox over IMAP and extracts the Spotify link using regex. The `/breach` and `/911` commands send alert emails via SMTP.

**Ephemeral vs. public responses** — some commands (like `/myrender` and `/workstation`) post ephemeral messages visible only to the caller since they contain personal or sensitive data. Others (like `/renders` and `/due`) post publicly to the channel.

---

## Project structure

```
dreambot/
├── projects.py       # All slash command definitions and Slack event handlers
├── backend.py        # ShotGrid queries, email handling, time utilities, render farm helpers
└── constants.py      # API tokens, credentials, and server config (not included in repo)
```

---

## Setup

1. Clone the repo
2. Install dependencies:
```bash
pip install slack-bolt slack-sdk shotgun-api3 pytz
```
3. Fill in the `constants.py` file with your tokens:
```python
token = "xoxb-your-bot-token"
signing_secret = "your-signing-secret"
xapp = "xapp-your-app-level-token"
email_pass = "your-gmail-app-password"
```
4. Configure your ShotGrid credentials in `backend.py`:
```python
SERVER_PATH = "https://your-studio.shotgunstudio.com"
SCRIPT_NAME = "your-script-name"
SCRIPT_KEY = "your-script-key"
```
5. Run the bot:
```bash
python projects.py
```

---

## Notes

This bot was built for and deployed in a live production environment at Mavericks VFX. Server paths, API keys, internal links, and email addresses have been removed or redacted from this public version. The constants file is excluded from the repository entirely.

---

## Built with

- Python 3
- Slack Bolt / Slack SDK
- ShotGrid API v3
- Deadline Connect
- Gmail IMAP / SMTP
