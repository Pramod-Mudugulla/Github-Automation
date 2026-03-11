# 🤖 GitHub Automation Agents

Automated GitHub contribution tools that keep your profile active and generate mini-projects — all on autopilot using **Windows Task Scheduler**.

> **What does this do?**
> - **Daily Commit Agent** — Makes 1–3 commits per day to a random repo's `.contributions` file
> - **Project Creator Agent** — Generates and pushes brand-new mini-projects to your GitHub at regular intervals

---

## 📑 Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Getting Your API Keys (Step-by-Step)](#-getting-your-api-keys-step-by-step)
   - [GitHub Personal Access Token](#1-github-personal-access-token-required)
   - [HuggingFace Token](#2-huggingface-token-optional)
3. [Installation](#-installation)
4. [Configuration](#-configuration)
5. [Running the Agents](#-running-the-agents)
6. [Setting Up Auto-Run with Task Scheduler](#-setting-up-auto-run-with-task-scheduler)
7. [Safety Controls](#-safety-controls)
8. [Project Structure](#-project-structure)
9. [Troubleshooting](#-troubleshooting)

---

## 🧰 Prerequisites

Before you start, make sure you have these installed:

| Tool       | What It Is                                       | Download Link                                                  |
| ---------- | ------------------------------------------------ | -------------------------------------------------------------- |
| **Python** | The programming language that runs the agents     | [python.org/downloads](https://www.python.org/downloads/)      |
| **Git**    | Version control tool (needed for cloning)         | [git-scm.com/downloads](https://git-scm.com/downloads)        |
| **GitHub** | A free account where your repos live              | [github.com/signup](https://github.com/signup)                 |

### How to Check If Python Is Installed

Open **Command Prompt** or **PowerShell** and type:
```
python --version
```
You should see something like `Python 3.10.x` or higher. If you get an error, download and install Python first.

> **⚠️ Important:** During Python installation, check the box that says **"Add Python to PATH"**. This lets you run `python` from anywhere.

---

## 🔑 Getting Your API Keys (Step-by-Step)

### 1. GitHub Personal Access Token (REQUIRED)

This token lets the agents read/write to your GitHub repos. Follow these steps carefully:

#### Step 1: Go to Token Settings
1. Log in to [github.com](https://github.com)
2. Click your **profile picture** (top-right corner) → **Settings**
3. Scroll down the left sidebar → click **Developer settings** (at the very bottom)
4. Click **Personal access tokens** → **Tokens (classic)**

   > ℹ️ There are two types of tokens: **Fine-grained** and **Classic**. We'll use **Classic** because it's simpler to set up.

#### Step 2: Generate a New Token
1. Click the **"Generate new token"** button → select **"Generate new token (classic)"**
2. You may be asked to confirm your password or use 2FA — do that

#### Step 3: Configure the Token
Fill in the fields as follows:

| Field          | What to Enter                                                        |
| -------------- | -------------------------------------------------------------------- |
| **Note**       | Give it a name like `GitHub Automation Agent`                        |
| **Expiration** | Choose **90 days**, **1 year**, or **No expiration** (your choice)   |

#### Step 4: Select Permissions (Scopes)

This is the most important part. Check **ONLY** these boxes:

| Scope           | What It Does                                    | Why We Need It            |
| --------------- | ----------------------------------------------- | ------------------------- |
| ✅ `repo`       | Full access to your repositories                | Read/write files & create repos |
| ✅ `delete_repo`| Ability to delete repositories                  | Optional — only if you want cleanup ability |

**Leave everything else unchecked.** You don't need `admin`, `gist`, `notifications`, etc.

> **🔒 Security Tip:** The fewer scopes you select, the safer your token is. The `repo` scope alone is enough for both agents to work. Only add `delete_repo` if you want the ability to remove auto-created projects later.

#### Step 5: Copy and Save Your Token
1. Click **"Generate token"** at the bottom
2. **⚠️ IMPORTANT:** Copy the token **immediately** — it looks like `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. **You will NEVER see this token again** after leaving the page. If you lose it, you'll need to create a new one

> **🚨 Never share your token or push it to GitHub!** Treat it like a password.

---

### 2. HuggingFace Token (OPTIONAL)

The **Project Creator Agent** can use a HuggingFace AI model to generate unique project ideas. Without this token, it falls back to a built-in list of 30+ pre-defined project ideas — so **this step is optional**.

#### Step 1: Create a HuggingFace Account
1. Go to [huggingface.co](https://huggingface.co)
2. Click **"Sign Up"** and create a free account

#### Step 2: Generate an Access Token
1. Click your **profile picture** (top-right) → **Settings**
2. Click **Access Tokens** in the left sidebar
3. Click **"New token"**

#### Step 3: Configure the Token

| Field          | What to Enter                                   |
| -------------- | ----------------------------------------------- |
| **Name**       | `GitHub Automation` (or anything you like)       |
| **Type**       | Select **`Read`** (this is all you need)         |

> **Why "Read" access?** We're only *using* (reading/running) pre-existing AI models hosted on HuggingFace. We're not uploading anything, so `Read` is sufficient and safer than `Write`.

| Token Type | What It Allows                           | Do You Need It?                |
| ---------- | ---------------------------------------- | ------------------------------ |
| **Read**   | Use models, download files               | ✅ Yes — this is what we need  |
| **Write**  | Upload models, create repos on HuggingFace | ❌ No — not needed            |

#### Step 4: Copy the Token
1. Click **"Generate"**
2. Copy the token — it looks like `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 📦 Installation

### Step 1: Clone This Repository

Open **Command Prompt** or **PowerShell** and run:

```bash
git clone https://github.com/Pramod-Mudugulla/Github-Automation.git
cd Github-Automation
```

### Step 2: Create a Virtual Environment

A virtual environment keeps this project's dependencies separate from your other Python projects:

```bash
python -m venv .venv
```

### Step 3: Activate the Virtual Environment

```bash
# On Windows (Command Prompt)
.venv\Scripts\activate

# On Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

You'll see `(.venv)` appear at the start of your terminal line — that means it's active.

### Step 4: Install Dependencies

```bash
pip install PyGithub python-dotenv requests
```

| Package          | What It Does                                    |
| ---------------- | ----------------------------------------------- |
| `PyGithub`       | Communicates with GitHub's API                  |
| `python-dotenv`  | Reads your API keys from the `.env` file        |
| `requests`       | Makes HTTP calls to HuggingFace's AI models     |

### Step 5: Create the `.env` File

Create a file named `.env` in the project folder (no filename, just the extension):

```
GITHUB_TOKEN=ghp_your_token_here
HF_TOKEN=hf_your_token_here
```

Replace the placeholder values with the tokens you copied earlier.

> **💡 Tip for beginners:** You can create this file by running:
> ```bash
> echo GITHUB_TOKEN=ghp_your_token_here > .env
> echo HF_TOKEN=hf_your_token_here >> .env
> ```
> Then open `.env` in any text editor and paste your real tokens.

---

## ⚙️ Configuration

All settings live in **`config.json`**. Here's what each one does:

### Daily Commit Agent Settings

```json
{
  "daily_commit": {
    "enabled": true,
    "username": "YOUR-GITHUB-USERNAME",
    "commit_count_range": [1, 3],
    "target_file": ".contributions",
    "exclude_forks": true,
    "commit_messages": [
      "docs: update activity log",
      "chore: update metadata",
      "docs: add daily notes"
    ]
  }
}
```

| Setting              | What It Does                                             | Default         |
| -------------------- | -------------------------------------------------------- | --------------- |
| `enabled`            | Turn the agent on (`true`) or off (`false`)              | `true`          |
| `username`           | **Your GitHub username** — change this!                  | —               |
| `commit_count_range` | Min and max commits per day                              | `[1, 3]`        |
| `target_file`        | The file it creates/updates in your repos                | `.contributions` |
| `exclude_forks`      | Skip repos you've forked from others                     | `true`          |
| `commit_messages`    | Random messages used for commits                         | (see above)     |

### Project Creator Agent Settings

```json
{
  "project_creator": {
    "enabled": true,
    "username": "YOUR-GITHUB-USERNAME",
    "simple_interval_days": 7,
    "complex_interval_days": 14,
    "hf_model": "HuggingFaceH4/zephyr-7b-beta",
    "languages": ["python", "javascript", "html-css"]
  }
}
```

| Setting                | What It Does                                            | Default                               |
| ---------------------- | ------------------------------------------------------- | ------------------------------------- |
| `enabled`              | Turn the agent on (`true`) or off (`false`)             | `false`                               |
| `username`             | **Your GitHub username** — change this!                 | —                                     |
| `simple_interval_days` | Days between simple projects (complexity 1–5)           | `7`                                   |
| `complex_interval_days`| Days between complex projects (complexity 6–10)         | `14`                                  |
| `hf_model`             | Which AI model generates ideas                          | `HuggingFaceH4/zephyr-7b-beta`       |
| `languages`            | Languages for generated projects                        | `["python", "javascript", "html-css"]`|

### Schedule Settings

```json
{
  "schedule": {
    "window_start_hour": 18,
    "window_end_hour": 22,
    "timezone": "Asia/Kolkata"
  }
}
```

| Setting             | What It Does                                          | Default           |
| ------------------- | ----------------------------------------------------- | ----------------- |
| `window_start_hour` | Earliest hour the agent can run (24h format)          | `18` (6 PM)       |
| `window_end_hour`   | Latest hour the agent can run (24h format)            | `22` (10 PM)      |
| `timezone`          | Your timezone                                         | `Asia/Kolkata`    |

---

## 🚀 Running the Agents

### Manual Run (Test It First!)

Always test manually before setting up auto-run:

```bash
# Activate the virtual environment first
.venv\Scripts\activate

# Run the Daily Commit Agent (use --now to skip the "already ran today" check)
python daily_commit.py --now

# Run the Project Creator Agent (use --now to skip the random sleep delay)
python project_creator.py --now
```

The `--now` flag means:
- **Daily Commit:** Skips the "already committed today" check
- **Project Creator:** Skips the random sleep timer (which normally waits 0–4 hours)

### Using the Batch Files

You can also double-click the `.bat` files:
- `daily_commit.bat` — Runs the daily commit agent
- `project_creator.bat` — Runs the project creator agent

---

## ⏰ Setting Up Auto-Run with Task Scheduler

This makes the agents run automatically every day without you doing anything.

### Step-by-Step for Daily Commit Agent

1. Press **Win + S** and search for **"Task Scheduler"** → open it
2. Click **"Create Basic Task..."** in the right panel
3. Fill in the wizard:

| Step               | What to Enter                              |
| ------------------ | ------------------------------------------ |
| **Name**           | `GitHub Daily Commit Agent`                |
| **Trigger**        | Select **Daily**                           |
| **Start Time**     | Set to **6:00 PM** (18:00)                 |
| **Action**         | Select **Start a program**                 |
| **Program/Script** | Full path to `daily_commit.bat`            |
| **Start in**       | The folder path, e.g. `D:\Github-Automation` |

4. Click **Finish**

### Step-by-Step for Project Creator Agent

Repeat the same steps with:

| Step               | What to Enter                              |
| ------------------ | ------------------------------------------ |
| **Name**           | `GitHub Project Creator Agent`             |
| **Trigger**        | Select **Daily**                           |
| **Start Time**     | Set to **6:30 PM** (18:30)                 |
| **Program/Script** | Full path to `project_creator.bat`         |

> **💡 Pro Tip:** In the task properties (double-click the task after creating it), go to the **Conditions** tab and uncheck **"Start the task only if the computer is on AC power"** — otherwise it won't run on a laptop running on battery.

---

## 🛡️ Safety Controls

### Kill Switch — `control.flag`

This file is the **master on/off switch** for both agents:

```
# Set to "on" to enable agents, "off" to disable
# Or simply delete this file to stop all agents
status=on
```

- Change `status=on` → `status=off` to **pause all agents**
- Delete the file entirely to **stop all agents**
- Both agents check this file before doing anything

### Per-Agent Toggle

Each agent has its own `enabled` setting in `config.json`:

```json
"daily_commit": { "enabled": true },   // ← turn on/off individually
"project_creator": { "enabled": false } // ← turn on/off individually
```

### What the Agents Touch

| Agent             | What It Modifies                                          | Impact Level |
| ----------------- | --------------------------------------------------------- | ------------ |
| Daily Commit      | Only the `.contributions` file in your repos              | 🟢 Very Low  |
| Project Creator   | Creates new public repos with template starter code       | 🟡 Low       |

---

## 📁 Project Structure

```
Github-Automation/
├── .env                    # Your secret API keys (never pushed to GitHub)
├── .gitignore              # Tells git to ignore .env, logs, etc.
├── config.json             # All agent settings
├── control.flag            # Master on/off kill switch
├── created_projects.json   # History of auto-created projects
├── daily_commit.py         # Daily Commit Agent script
├── daily_commit.bat        # Windows batch file to run daily agent
├── project_creator.py      # Project Creator Agent script
├── project_creator.bat     # Windows batch file to run project creator
├── templates/              # Project template categories
│   ├── algorithm/
│   ├── api-wrapper/
│   ├── cli-tool/
│   ├── data-viz/
│   ├── utility/
│   └── web-page/
└── logs/                   # Agent execution logs (auto-created)
    ├── daily_commit.log
    └── project_creator.log
```

---

## 🔧 Troubleshooting

### "Bad credentials" Error
- Your `GITHUB_TOKEN` in `.env` is invalid or expired
- Go to [GitHub Settings → Tokens](https://github.com/settings/tokens) and generate a new one
- Make sure there are **no extra spaces** around the token in `.env`

### "GITHUB_TOKEN not set" Error
- Make sure the `.env` file exists in the project root folder
- Make sure it has `GITHUB_TOKEN=ghp_...` (no quotes around the value)

### "Not a git repository" Error
- You're running commands from the wrong folder
- Make sure you `cd` into the project folder first

### Agent Says "Already committed today"
- This is normal! The daily agent only runs once per day
- Use `python daily_commit.py --now` to force a run for testing

### Task Scheduler Isn't Running the Agent
- Open Task Scheduler → find your task → check **"Last Run Result"**
- Make sure the **"Start in"** path is correct
- Make sure the `.bat` file path has no typos
- Try running the `.bat` file manually first by double-clicking it

### HuggingFace API Fails
- This is fine — the Project Creator will automatically use its built-in list of 30+ project ideas
- If you want the AI feature, check your `HF_TOKEN` in `.env`

---

## 📜 License

MIT — use it however you like.

---

<p align="center">
  Made with 🤖 by <a href="https://github.com/Pramod-Mudugulla">Pramod Mudugulla</a>
</p>
