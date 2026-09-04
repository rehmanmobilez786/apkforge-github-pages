"""Provision the Android SDK needed by uploaded Gradle projects.

The Replit runtime has Java but does not guarantee an Android SDK. Android
projects declare their compile SDK in Gradle files, so the builder installs
only the matching platform and build-tools into a cached workspace directory.
"""

from __future__ import annotations

import fcntl
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from .builder import BuildError

COMMAND_LINE_TOOLS_URL = (
    "https://dl.google.com/android/repository/"
    "commandlinetools-linux-11076708_latest.zip"
)
DEFAULT_COMPILE_SDK = 35
DEFAULT_BUILD_TOOLS = "35.0.0"
SDK_LOCK_NAME = ".sdk-install.lock"


def ensure_android_sdk(project_dir: Path) -> Path:
    """Ensure the SDK packages required by *project_dir* are available."""
    sdk_root = _sdk_root()
    compile_sdk = _find_compile_sdk(project_dir) or DEFAULT_COMPILE_SDK
    build_tools = _find_build_tools_version(project_dir) or DEFAULT_BUILD_TOOLS
    platform_path = sdk_root / "platforms" / f"android-{compile_sdk}"
    build_tools_path = sdk_root / "build-tools" / build_tools

    if platform_path.is_dir() and build_tools_path.is_dir():
        _set_sdk_environment(sdk_root)
        return sdk_root

    sdk_root.mkdir(parents=True, exist_ok=True)
    lock_path = sdk_root / SDK_LOCK_NAME
    with lock_path.open("w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        if not _sdkmanager_path(sdk_root).is_file():
            _install_command_line_tools(sdk_root)

        packages = []
        if not platform_path.is_dir():
            packages.append(f"platforms;android-{compile_sdk}")
        if not build_tools_path.is_dir():
            packages.append(f"build-tools;{build_tools}")
        if packages:
            _install_sdk_packages(sdk_root, packages)

    if not platform_path.is_dir():
        raise BuildError(
            f"Android SDK platform android-{compile_sdk} was not installed. "
            "Check the project's compileSdk value and try again."
        )
    if not build_tools_path.is_dir():
        raise BuildError(
            f"Android build-tools {build_tools} was not installed. "
            "Check the project's buildToolsVersion value and try again."
        )
    _set_sdk_environment(sdk_root)
    return sdk_root


def _sdk_root() -> Path:
    configured = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(os.environ.get("APK_BUILDER_SDK_ROOT", "/tmp/apk-builder-android-sdk"))


def _set_sdk_environment(sdk_root: Path) -> None:
    os.environ["ANDROID_SDK_ROOT"] = str(sdk_root)
    os.environ["ANDROID_HOME"] = str(sdk_root)


def _sdkmanager_path(sdk_root: Path) -> Path:
    return sdk_root / "cmdline-tools" / "latest" / "bin" / "sdkmanager"


def _install_command_line_tools(sdk_root: Path) -> None:
    tools_dir = sdk_root / "cmdline-tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="android-cmdline-tools-") as temp_dir:
        archive = Path(temp_dir) / "command-line-tools.zip"
        try:
            urllib.request.urlretrieve(COMMAND_LINE_TOOLS_URL, archive)
        except (OSError, urllib.error.URLError) as exc:
            raise BuildError(
                "Could not download the Android SDK command-line tools. "
                "Check the build server's internet access and try again."
            ) from exc

        extracted = Path(temp_dir) / "extracted"
        extracted.mkdir()
        try:
            with zipfile.ZipFile(archive) as zipped:
                zipped.extractall(extracted)
        except (OSError, zipfile.BadZipFile) as exc:
            raise BuildError(
                "The Android SDK command-line tools download was incomplete. "
                "Please retry the build."
            ) from exc

        source = extracted / "cmdline-tools"
        if not (source / "bin" / "sdkmanager").is_file():
            raise BuildError(
                "The Android SDK command-line tools archive had an unexpected layout."
            )
        target = tools_dir / "latest"
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(source), target)
        for executable in (target / "bin").iterdir():
            if executable.is_file():
                executable.chmod(executable.stat().st_mode | 0o111)


def _install_sdk_packages(sdk_root: Path, packages: list[str]) -> None:
    sdkmanager = _sdkmanager_path(sdk_root)
    _run_sdkmanager(
        sdkmanager,
        sdk_root,
        ["--licenses"],
        input_text=("y\n" * 100),
    )
    _run_sdkmanager(sdkmanager, sdk_root, packages)


def _run_sdkmanager(
    sdkmanager: Path,
    sdk_root: Path,
    arguments: list[str],
    *,
    input_text: str = "",
) -> None:
    command = [str(sdkmanager), f"--sdk_root={sdk_root}", *arguments]
    try:
        completed = subprocess.run(
            command,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as exc:
        raise BuildError(f"Could not start Android SDK manager: {exc}") from exc
    if completed.returncode != 0:
        details = completed.stdout.strip()[-2_000:]
        raise BuildError(
            "Android SDK setup failed."
            + (f"\n{details}" if details else " Check the requested SDK version.")
        )


def _find_compile_sdk(project_dir: Path) -> int | None:
    patterns = (
        re.compile(r"\bcompileSdk(?:Version)?\s*(?:=|\s)\s*[\"']?(\d+)", re.I),
        re.compile(r"\bcompileSdk\s*=\s*[\"']?android-(\d+)", re.I),
    )
    for gradle_file in project_dir.rglob("build.gradle*"):
        if "build" in gradle_file.parts:
            continue
        try:
            contents = gradle_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in patterns:
            match = pattern.search(contents)
            if match:
                return int(match.group(1))
    return None


def _find_build_tools_version(project_dir: Path) -> str | None:
    pattern = re.compile(r"\bbuildToolsVersion\s*(?:=|\s)\s*[\"']([^\"']+)", re.I)
    for gradle_file in project_dir.rglob("build.gradle*"):
        if "build" in gradle_file.parts:
            continue
        try:
            contents = gradle_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        match = pattern.search(contents)
        if match:
            return match.group(1).strip()
    return None