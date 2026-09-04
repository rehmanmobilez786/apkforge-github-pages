"""Fetch public Git repositories as build sources."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from .builder import BuildError

ALLOWED_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}
GIT_CLONE_TIMEOUT_SECONDS = 300


def validate_repository_url(repository_url: str) -> str:
    """Validate and normalize a public repository URL."""
    parsed = urlparse(repository_url.strip())
    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() not in ALLOWED_HOSTS
        or parsed.username
        or parsed.password
        or parsed.port
        or parsed.query
        or parsed.fragment
    ):
        raise BuildError(
            "Repository URL must be an HTTPS public GitHub, GitLab, or Bitbucket "
            "repository link."
        )

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2:
        raise BuildError(
            "Repository URL must point to the repository root, for example "
            "https://github.com/owner/project."
        )
    owner, repository = parts
    if repository.endswith(".git"):
        repository = repository[:-4]
    if not owner or not repository:
        raise BuildError("Repository URL must include both an owner and repository name.")

    return urlunparse(("https", parsed.netloc.lower(), f"/{owner}/{repository}", "", "", ""))


def clone_repository(repository_url: str, destination: Path) -> Path:
    """Shallow-clone the latest default branch into *destination*."""
    normalized_url = validate_repository_url(repository_url)
    if shutil.which("git") is None:
        raise BuildError("Git is not available on the build server.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--no-tags",
        normalized_url,
        str(destination),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=GIT_CLONE_TIMEOUT_SECONDS,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise BuildError(
            "Repository download timed out after five minutes. "
            "Check the repository size and try again."
        ) from exc
    except OSError as exc:
        raise BuildError(f"Could not start Git: {exc}") from exc

    if completed.returncode != 0:
        details = completed.stdout.strip()[-2_000:]
        raise BuildError(
            "Could not download the repository. Make sure the link is public and "
            "points to a Git repository."
            + (f"\n{details}" if details else "")
        )
    return destination