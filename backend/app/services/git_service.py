import os
import shutil
import tempfile
from typing import Optional
from git import Repo, GitCommandError


class GitService:
    def __init__(self, storage_path: str, github_token: Optional[str] = None):
        self.storage_path = storage_path
        self.github_token = github_token
        os.makedirs(storage_path, exist_ok=True)

    def clone_repository(self, repo_url: str, branch: Optional[str] = None) -> str:
        repo_name = self._extract_repo_name(repo_url)
        local_path = tempfile.mkdtemp(prefix=f"{repo_name}_", dir=self.storage_path)

        if self.github_token and "github.com" in repo_url:
            repo_url = repo_url.replace("https://github.com/", f"https://x-access-token:{self.github_token}@github.com/")

        branches_to_try = [branch] if branch else []
        if not branches_to_try:
            branches_to_try = ["main", "master"]
        elif branch == "main":
            branches_to_try = ["main", "master"]
        elif branch == "master":
            branches_to_try = ["master", "main"]

        last_error = None
        for b in branches_to_try:
            try:
                Repo.clone_from(repo_url, local_path, branch=b, depth=1)
                return local_path
            except GitCommandError as e:
                last_error = e
                if os.path.exists(local_path):
                    shutil.rmtree(local_path, ignore_errors=True)
                continue

        raise Exception(f"Failed to clone repository. Tried branches: {branches_to_try}. Error: {last_error}")

    def get_contributors(self, repo_path: str) -> list:
        contributors = {}
        try:
            repo = Repo(repo_path)
            for commit in repo.iter_commits():
                author = str(commit.author)
                if author not in contributors:
                    contributors[author] = {
                        "name": author,
                        "email": str(commit.author.email),
                        "commits": 0,
                        "last_commit": str(commit.committed_datetime),
                    }
                contributors[author]["commits"] += 1
        except Exception:
            pass
        return list(contributors.values())

    def get_repo_info(self, repo_path: str) -> dict:
        info = {
            "commits": 0,
            "branches": [],
            "tags": [],
            "last_commit": None,
        }
        try:
            repo = Repo(repo_path)
            info["commits"] = sum(1 for _ in repo.iter_commits())
            info["branches"] = [str(b) for b in repo.branches]
            info["tags"] = [str(t) for t in repo.tags]
            if repo.head.commit:
                info["last_commit"] = {
                    "hash": str(repo.head.commit.hexsha)[:8],
                    "message": repo.head.commit.message.strip(),
                    "author": str(repo.head.commit.author),
                    "date": str(repo.head.commit.committed_datetime),
                }
        except Exception:
            pass
        return info

    def get_repo_size(self, repo_path: str) -> int:
        total = 0
        for dirpath, dirnames, filenames in os.walk(repo_path):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    continue
        return total

    def _extract_repo_name(self, repo_url: str) -> str:
        name = repo_url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name

    def cleanup(self, repo_path: str):
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
