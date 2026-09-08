"""Synchronize the README with current GitHub stargazers."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

START = "<!-- STARGAZERS:START -->"
END = "<!-- STARGAZERS:END -->"


def fetch_users(repository: str) -> list[str]:
    """Fetch every page; failures leave the README untouched."""
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise ValueError("invalid repository")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "RuleShift-stars"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    users = set()
    page = 1
    while True:
        request = Request(f"https://api.github.com/repos/{repository}/stargazers?per_page=100&page={page}", headers=headers)
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError("invalid API response")
        for user in batch:
            login = user["login"]
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", login):
                raise ValueError("invalid login")
            users.add(login)
        if len(batch) < 100:
            return sorted(users, key=str.casefold)
        page += 1


def render(readme: str, users: list[str]) -> str:
    """Replace only the uniquely marked block."""
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError("missing or duplicate markers")
    before, remainder = readme.split(START)
    _, after = remainder.split(END)
    links = " · ".join(f"[@{u}](https://github.com/{u})" for u in users)
    return f"{before}{START}\n\n感谢 {len(users)} 位 Star 用户！\n\n{links or '期待你的第一颗 Star。'}\n\n{END}{after}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "Darvin-shaw/RuleShift"))
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    path = root / "README.md"
    original = path.read_text(encoding="utf-8")
    updated = render(original, fetch_users(args.repository))
    if updated == original:
        print("Star list unchanged")
        return
    path.write_text(updated, encoding="utf-8", newline="\n")
    if args.summary:
        date = datetime.now(timezone.utc).date().isoformat()
        run_id = os.environ.get("GITHUB_RUN_ID", "local")
        summary = root / "docs/git-diffs" / f"{date}-star-list-{run_id}.md"
        summary.write_text(f"# Star 名单同步\n\n日期：{date}（UTC）\n\n涉及文件：README.md、本总结。\n\n变更：同步 GitHub 当前 Star 用户。\n\n影响：新增 Star 加入，取消 Star 移除；仅变更展示名单。\n", encoding="utf-8", newline="\n")
    print("Star list updated")


if __name__ == "__main__":
    main()
