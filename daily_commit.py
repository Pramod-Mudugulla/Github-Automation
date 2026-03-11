"""
GitHub Daily Commit Agent
Automatically makes 1-3 commits to a random repo's .contributions file daily.
Designed to run via Windows Task Scheduler at 6 PM IST, with random sleep
to spread activity across 6-10 PM IST window.
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from base64 import b64decode, b64encode

from dotenv import load_dotenv
from github import Github, Auth, GithubException

# ─── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ─── Logging ────────────────────────────────────────────────────────────────
# Custom stream handler that handles encoding errors gracefully
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
        logging.FileHandler(LOG_DIR / "daily_commit.log", encoding="utf-8"),
        SafeStreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("daily_commit")

# ─── IST timezone ───────────────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))


def load_config():
    """Load config.json and return the daily_commit section."""
    config_path = BASE_DIR / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    """Save updated config back to config.json."""
    config_path = BASE_DIR / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def check_kill_switch():
    """Check control.flag — return True if agents are enabled."""
    flag_path = BASE_DIR / "control.flag"
    if not flag_path.exists():
        log.info("control.flag not found — exiting.")
        return False
    content = flag_path.read_text(encoding="utf-8").strip()
    if "status=on" not in content:
        log.info("control.flag is set to off — exiting.")
        return False
    return True


def already_ran_today(config):
    """Check if the agent already committed today."""
    dc = config.get("daily_commit", {})
    last_date = dc.get("last_committed_date", "")
    today = datetime.now(IST).strftime("%Y-%m-%d")
    return last_date == today


def get_all_repos(g, username, exclude_forks=True):
    """Fetch all non-fork repos for the user."""
    repos = []
    for repo in g.get_user(username).get_repos():
        if exclude_forks and repo.fork:
            continue
        if repo.archived:
            continue
        repos.append(repo)
    return repos


def pick_random_repo(repos, last_committed_repo):
    """Pick a random repo, avoiding the last committed one if possible."""
    if len(repos) == 0:
        return None
    if len(repos) == 1:
        return repos[0]

    # Filter out the last committed repo
    candidates = [r for r in repos if r.name != last_committed_repo]
    if not candidates:
        candidates = repos  # fallback if all filtered out

    return random.choice(candidates)


def generate_contribution_content():
    """Generate a timestamped log entry for the .contributions file."""
    now = datetime.now(IST)
    entries = [
        f"📝 Activity log updated — {now.strftime('%Y-%m-%d %H:%M:%S IST')}",
        f"🔧 Routine maintenance check — {now.strftime('%Y-%m-%d %H:%M:%S IST')}",
        f"📊 Daily sync — {now.strftime('%Y-%m-%d %H:%M:%S IST')}",
        f"✅ Status check completed — {now.strftime('%Y-%m-%d %H:%M:%S IST')}",
        f"📋 Notes updated — {now.strftime('%Y-%m-%d %H:%M:%S IST')}",
        f"🔄 Metadata refresh — {now.strftime('%Y-%m-%d %H:%M:%S IST')}",
    ]
    return random.choice(entries)


def commit_to_repo(repo, target_file, commit_message):
    """Create or update the target file in the repo via GitHub API."""
    try:
        # Try to get existing file
        contents = repo.get_contents(target_file, ref=repo.default_branch)
        existing_content = b64decode(contents.content).decode("utf-8")
        new_line = generate_contribution_content()
        updated_content = existing_content.rstrip("\n") + "\n" + new_line + "\n"

        repo.update_file(
            path=target_file,
            message=commit_message,
            content=updated_content,
            sha=contents.sha,
            branch=repo.default_branch,
        )
        log.info(f"  ✅ Updated '{target_file}' in {repo.full_name}")

    except GithubException as e:
        if e.status == 404:
            # File doesn't exist — create it
            header = "# Contribution Activity Log\n\n"
            header += "This file tracks repository activity.\n\n"
            new_line = generate_contribution_content()
            content = header + new_line + "\n"

            repo.create_file(
                path=target_file,
                message=commit_message,
                content=content,
                branch=repo.default_branch,
            )
            log.info(f"  ✅ Created '{target_file}' in {repo.full_name}")
        else:
            log.error(f"  ❌ GitHub API error for {repo.full_name}: {e}")
            raise


def main():
    log.info("=" * 60)
    log.info("Daily Commit Agent — Starting")
    log.info("=" * 60)

    # 1. Kill switch
    if not check_kill_switch():
        return

    # 2. Load config
    config = load_config()
    dc = config["daily_commit"]

    if not dc.get("enabled", True):
        log.info("Daily commit agent is disabled in config — exiting.")
        return

    # 3. Check GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log.error("GITHUB_TOKEN not set in .env — exiting.")
        return

    # 4. Check if already ran today (skip with --now for manual testing)
    if "--now" not in sys.argv:
        if already_ran_today(config):
            log.info("Already committed today — skipping.")
            return
    else:
        log.info("--now flag detected, bypassing daily check.")

    # 5. Connect to GitHub
    g = Github(auth=Auth.Token(token))

    try:
        # 6. Fetch repos
        username = dc["username"]
        exclude_forks = dc.get("exclude_forks", True)
        repos = get_all_repos(g, username, exclude_forks)
        log.info(f"Found {len(repos)} repos for {username}")

        if not repos:
            log.warning("No repos found — exiting.")
            return

        # 7. Pick random repo
        last_committed = dc.get("last_committed_repo", "")
        repo = pick_random_repo(repos, last_committed)
        log.info(f"Selected repo: {repo.full_name}")

        # 8. Random commit count (1-3)
        count_range = dc.get("commit_count_range", [1, 3])
        commit_count = random.randint(count_range[0], count_range[1])
        log.info(f"Will make {commit_count} commit(s)")

        # 9. Make commits
        target_file = dc.get("target_file", ".contributions")
        messages = dc.get("commit_messages", ["docs: update activity log"])

        for i in range(commit_count):
            msg = random.choice(messages)
            log.info(f"  Commit {i + 1}/{commit_count}: '{msg}'")
            commit_to_repo(repo, target_file, msg)

            # Small delay between multiple commits
            if i < commit_count - 1:
                delay = random.randint(5, 30)
                log.info(f"  Waiting {delay}s before next commit...")
                time.sleep(delay)

        # 10. Update last committed repo and date
        config["daily_commit"]["last_committed_repo"] = repo.name
        config["daily_commit"]["last_committed_date"] = datetime.now(IST).strftime("%Y-%m-%d")
        save_config(config)

        log.info(f"✅ Done! Made {commit_count} commit(s) to {repo.full_name}")

    except Exception as e:
        log.error(f"❌ Error: {e}", exc_info=True)
    finally:
        g.close()

    log.info("=" * 60)


if __name__ == "__main__":
    main()
