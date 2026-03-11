"""
GitHub Project Creator Agent
Automatically creates small, unique GitHub projects at intervals determined
by complexity scoring from a free HuggingFace LLM.
- Simple projects (score 1-5) → every 7 days
- Complex projects (score 6-10) → every 14 days
"""

import os
import sys
import json
import time
import random
import logging
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from github import Github, Auth, GithubException

# ─── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ─── Logging ────────────────────────────────────────────────────────────────
class SafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            msg = msg.encode("ascii", errors="replace").decode("ascii")
            stream.write(msg + self.terminator)
            self.flush()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "project_creator.log", encoding="utf-8"),
        SafeStreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("project_creator")

IST = timezone(timedelta(hours=5, minutes=30))

# ─── Fallback project ideas (used when HF API is unavailable) ───────────
FALLBACK_IDEAS = [
    {"name": "markdown-table-generator", "description": "CLI tool that converts CSV data into formatted markdown tables", "language": "python", "complexity": 3},
    {"name": "color-palette-extractor", "description": "Extract dominant color palettes from images using k-means clustering", "language": "python", "complexity": 5},
    {"name": "json-schema-validator", "description": "Lightweight JSON schema validator with clear error reporting", "language": "python", "complexity": 4},
    {"name": "git-stats-dashboard", "description": "HTML dashboard showing git repository statistics and charts", "language": "html-css", "complexity": 5},
    {"name": "pomodoro-timer-cli", "description": "Command-line Pomodoro timer with sound notifications", "language": "python", "complexity": 3},
    {"name": "api-rate-limiter", "description": "Decorator-based API rate limiter for Python applications", "language": "python", "complexity": 4},
    {"name": "env-diff-checker", "description": "Compare two .env files and highlight differences", "language": "python", "complexity": 2},
    {"name": "readme-generator", "description": "Auto-generate README.md from project structure and docstrings", "language": "python", "complexity": 5},
    {"name": "log-parser-analyzer", "description": "Parse and analyze log files with configurable pattern matching", "language": "python", "complexity": 4},
    {"name": "weather-widget", "description": "Minimal weather widget using a free weather API", "language": "javascript", "complexity": 4},
    {"name": "bookmark-organizer", "description": "CLI tool to organize and categorize browser bookmarks from exported HTML", "language": "python", "complexity": 4},
    {"name": "regex-tester-web", "description": "Simple web-based regex tester with live highlighting", "language": "html-css", "complexity": 3},
    {"name": "file-organizer-script", "description": "Automatically organize files in a directory by extension and date", "language": "python", "complexity": 3},
    {"name": "dependency-graph-viz", "description": "Visualize Python package dependencies as an interactive graph", "language": "python", "complexity": 6},
    {"name": "text-diff-viewer", "description": "Web-based side-by-side text diff viewer", "language": "html-css", "complexity": 4},
    {"name": "sqlite-query-builder", "description": "Fluent query builder for SQLite with Python", "language": "python", "complexity": 6},
    {"name": "cron-expression-parser", "description": "Parse and describe cron expressions in human-readable format", "language": "python", "complexity": 3},
    {"name": "http-status-lookup", "description": "CLI tool and library for looking up HTTP status codes with descriptions", "language": "python", "complexity": 2},
    {"name": "password-strength-meter", "description": "Interactive web-based password strength analyzer", "language": "javascript", "complexity": 3},
    {"name": "csv-to-json-converter", "description": "Robust CSV to JSON converter with type inference", "language": "python", "complexity": 3},
    {"name": "simple-chatbot-framework", "description": "Rule-based chatbot framework with pattern matching", "language": "python", "complexity": 5},
    {"name": "image-resizer-batch", "description": "Batch image resizer with quality settings and format conversion", "language": "python", "complexity": 4},
    {"name": "terminal-progress-bar", "description": "Customizable progress bar library for terminal applications", "language": "python", "complexity": 3},
    {"name": "url-shortener-api", "description": "Simple URL shortener API with redirect tracking", "language": "python", "complexity": 6},
    {"name": "markdown-slide-presenter", "description": "Convert markdown files into slide presentations in the browser", "language": "javascript", "complexity": 6},
    {"name": "data-faker-generator", "description": "Generate realistic fake data for testing with customizable schemas", "language": "python", "complexity": 5},
    {"name": "system-health-monitor", "description": "CLI dashboard showing CPU, memory, disk, and network stats", "language": "python", "complexity": 5},
    {"name": "qr-code-generator-web", "description": "Web app to generate and customize QR codes", "language": "html-css", "complexity": 4},
    {"name": "langchain-doc-summarizer", "description": "Document summarizer using LangChain and local LLM", "language": "python", "complexity": 7},
    {"name": "multi-agent-task-planner", "description": "Multi-agent system for breaking down and planning complex tasks", "language": "python", "complexity": 8},
]

# ─── Project templates for file generation ──────────────────────────────────

PYTHON_TEMPLATE = {
    "main.py": '''"""
{description}
"""

import argparse
import sys


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="{description}")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    print("{name} — running...")
    # TODO: Implement core logic
    print("Done!")


if __name__ == "__main__":
    main()
''',
    "requirements.txt": "# Dependencies for {name}\n",
    "README.md": '''# {name}

{description}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## License

MIT
''',
    ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/\n.venv/\n",
}

JAVASCRIPT_TEMPLATE = {
    "index.js": '''/**
 * {description}
 */

function main() {{
  console.log("{name} — running...");
  // TODO: Implement core logic
  console.log("Done!");
}}

main();
''',
    "package.json": '''{{"name": "{name}", "version": "1.0.0", "description": "{description}", "main": "index.js", "scripts": {{"start": "node index.js", "test": "echo \\"No tests yet\\""}}, "license": "MIT"}}
''',
    "README.md": '''# {name}

{description}

## Installation

```bash
npm install
```

## Usage

```bash
npm start
```

## License

MIT
''',
    ".gitignore": "node_modules/\n.env\n",
}

HTML_TEMPLATE = {
    "index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>{name}</h1>
        <p>{description}</p>
    </div>
    <script src="script.js"></script>
</body>
</html>
''',
    "style.css": '''* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e0e0e0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.container {{
    text-align: center;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}}

h1 {{
    font-size: 2rem;
    margin-bottom: 1rem;
    background: linear-gradient(90deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
''',
    "script.js": '''// {description}
document.addEventListener("DOMContentLoaded", () => {{
    console.log("{name} loaded!");
}});
''',
    "README.md": '''# {name}

{description}

## Setup

Open `index.html` in your browser.

## License

MIT
''',
}


def load_config():
    config_path = BASE_DIR / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    config_path = BASE_DIR / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_created_projects():
    path = BASE_DIR / "created_projects.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_created_projects(data):
    path = BASE_DIR / "created_projects.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_kill_switch():
    flag_path = BASE_DIR / "control.flag"
    if not flag_path.exists():
        log.info("control.flag not found — exiting.")
        return False
    content = flag_path.read_text(encoding="utf-8").strip()
    if "status=on" not in content:
        log.info("control.flag is set to off — exiting.")
        return False
    return True


def random_sleep(config):
    schedule = config.get("schedule", {})
    window_start = schedule.get("window_start_hour", 18)
    window_end = schedule.get("window_end_hour", 22)
    window_minutes = (window_end - window_start) * 60

    sleep_minutes = random.randint(0, window_minutes)
    log.info(f"Sleeping for {sleep_minutes} minutes to randomize execution time...")
    time.sleep(sleep_minutes * 60)


def query_huggingface(prompt, model, hf_token=None):
    """Query HuggingFace Inference API for a text generation response."""
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Content-Type": "application/json"}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.8,
            "return_full_text": False,
        },
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        return ""
    except Exception as e:
        log.warning(f"HuggingFace API failed: {e}")
        return None


def generate_project_idea_from_llm(existing_names, config):
    """Use HuggingFace LLM to generate a unique project idea."""
    pc = config["project_creator"]
    model = pc.get("hf_model", "HuggingFaceH4/zephyr-7b-beta")
    hf_token = os.getenv("HF_TOKEN", "")
    languages = pc.get("languages", ["python"])

    existing_list = ", ".join(existing_names[-20:]) if existing_names else "none yet"
    lang_list = ", ".join(languages)

    system_msg = "You generate coding project ideas. Respond with valid JSON only."
    user_msg = (
        "Generate ONE unique small coding project idea (a practical utility, tool, or demo). "
        "It must be different from: " + existing_list + ". "
        "Language must be one of: " + lang_list + ". "
        'Respond ONLY with JSON: {"name": "kebab-case-name", "description": "One sentence", "language": "python", "complexity": 5}. '
        "Complexity 1-5 = simple (CLI, script, static page, basic RAG, basic agent). "
        "Complexity 6-10 = complex (full-stack, ML pipeline, multi-agent)."
    )

    SYS_TAG = "<" + "|system|" + ">"
    END_TAG = "<" + "/s" + ">"
    USR_TAG = "<" + "|user|" + ">"
    AST_TAG = "<" + "|assistant|" + ">"

    prompt = (
        SYS_TAG + "\n" + system_msg + "\n" + END_TAG + "\n"
        + USR_TAG + "\n" + user_msg + "\n" + END_TAG + "\n"
        + AST_TAG + "\n"
    )

    response = query_huggingface(prompt, model, hf_token if hf_token else None)

    if response:
        try:
            import re
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                idea = json.loads(json_match.group())
                if all(k in idea for k in ["name", "description", "language", "complexity"]):
                    idea["complexity"] = max(1, min(10, int(idea["complexity"])))
                    log.info(f"LLM generated idea: {idea['name']} (complexity: {idea['complexity']})")
                    return idea
        except (json.JSONDecodeError, ValueError) as e:
            log.warning(f"Failed to parse LLM response: {e}")

    return None


def generate_project_idea_fallback(existing_names):
    """Fallback: pick from pre-defined ideas pool."""
    available = [idea for idea in FALLBACK_IDEAS if idea["name"] not in existing_names]
    if not available:
        # All ideas used — generate a variant
        base = random.choice(FALLBACK_IDEAS)
        suffix = random.choice(["v2", "lite", "plus", "mini", "pro"])
        variant = base.copy()
        variant["name"] = f"{base['name']}-{suffix}"
        return variant
    return random.choice(available)


def should_create_project(config, created_data):
    """Determine if enough days have passed based on last project's complexity."""
    pc = config["project_creator"]
    last_created = pc.get("last_created", "")

    if not last_created:
        return True  # Never created — go ahead

    last_date = datetime.strptime(last_created, "%Y-%m-%d").date()
    today = datetime.now(IST).date()
    days_elapsed = (today - last_date).days

    # Check interval based on last project's complexity
    last_complexity = pc.get("last_complexity", 3)
    if last_complexity <= 5:
        interval = pc.get("simple_interval_days", 7)
    else:
        interval = pc.get("complex_interval_days", 14)

    log.info(f"Last created: {last_created}, days elapsed: {days_elapsed}, "
             f"required interval: {interval} (complexity {last_complexity})")

    return days_elapsed >= interval


def get_existing_repo_names(g, username):
    """Get names of all existing repos."""
    names = set()
    for repo in g.get_user(username).get_repos():
        names.add(repo.name)
    return names


def get_template_files(idea):
    """Pick the right template and fill in placeholders."""
    lang = idea.get("language", "python").lower()
    name = idea["name"]
    desc = idea["description"]

    if lang in ("javascript", "js"):
        template = JAVASCRIPT_TEMPLATE
    elif lang in ("html-css", "html", "web"):
        template = HTML_TEMPLATE
    else:
        template = PYTHON_TEMPLATE

    files = {}
    for filename, content in template.items():
        files[filename] = content.format(name=name, description=desc)
    return files


def create_github_repo(g, username, idea):
    """Create a new GitHub repository and push template files."""
    user = g.get_user()
    repo_name = idea["name"]
    description = idea["description"]

    # Create the repo
    repo = user.create_repo(
        name=repo_name,
        description=description,
        auto_init=False,
        private=False,
    )
    log.info(f"  Created repo: {repo.full_name}")

    # Push template files
    files = get_template_files(idea)
    for filename, content in files.items():
        repo.create_file(
            path=filename,
            message=f"Initial commit: add {filename}",
            content=content,
            branch="main",
        )
        log.info(f"  Pushed: {filename}")

    return repo


def main():
    log.info("=" * 60)
    log.info("Project Creator Agent — Starting")
    log.info("=" * 60)

    # 1. Kill switch
    if not check_kill_switch():
        return

    # 2. Load config
    config = load_config()
    pc = config["project_creator"]

    if not pc.get("enabled", True):
        log.info("Project creator agent is disabled in config — exiting.")
        return

    # 3. GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log.error("GITHUB_TOKEN not set in .env — exiting.")
        return

    # 4. Random sleep (skip with --now)
    if "--now" not in sys.argv:
        random_sleep(config)
    else:
        log.info("--now flag detected, skipping random sleep.")

    # 5. Load project history
    created_data = load_created_projects()
    existing_names = [p["name"] for p in created_data.get("projects", [])]

    # 6. Check if it's time to create
    if not should_create_project(config, created_data):
        log.info("Not enough days elapsed — skipping creation.")
        return

    # 7. Connect to GitHub
    g = Github(auth=Auth.Token(token))

    try:
        username = pc["username"]
        github_repo_names = get_existing_repo_names(g, username)
        all_existing = set(existing_names) | github_repo_names

        # 8. Generate project idea
        log.info("Generating project idea...")
        idea = generate_project_idea_from_llm(list(all_existing), config)

        if idea is None:
            log.info("LLM unavailable — using fallback ideas.")
            idea = generate_project_idea_fallback(list(all_existing))

        # Ensure unique name
        while idea["name"] in all_existing:
            idea["name"] = idea["name"] + "-" + str(random.randint(10, 99))

        log.info(f"Project idea: {idea['name']} ({idea['language']}, complexity: {idea['complexity']})")

        # 9. Create the repo
        create_github_repo(g, username, idea)

        # 10. Update records
        now_str = datetime.now(IST).strftime("%Y-%m-%d")
        created_data.setdefault("projects", []).append({
            "name": idea["name"],
            "description": idea["description"],
            "language": idea["language"],
            "complexity": idea["complexity"],
            "created_date": now_str,
        })
        save_created_projects(created_data)

        config["project_creator"]["last_created"] = now_str
        config["project_creator"]["last_complexity"] = idea["complexity"]
        save_config(config)

        log.info(f"✅ Done! Created project: {idea['name']}")

    except Exception as e:
        log.error(f"❌ Error: {e}", exc_info=True)
    finally:
        g.close()

    log.info("=" * 60)


if __name__ == "__main__":
    main()
