"""Core Gradle and APK discovery operations."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class BuildError(RuntimeError):
    """Raised when a project cannot be built or an APK cannot be found."""


@dataclass(frozen=True)
class BuildResult:
    """Details about a completed APK build."""

    apk_path: Path
    command: tuple[str, ...]


def module_to_path(module: str) -> Path:
    """Convert Gradle module notation such as :mobile:app to a filesystem path."""
    normalized = module.strip().strip(":").replace("\\", "/").replace(":", "/")
    if not normalized:
        return Path(".")
    return Path(*(part for part in normalized.split("/") if part))


def module_to_gradle_path(module: str) -> str:
    """Convert a module name or path to Gradle's colon-separated notation."""
    normalized = module.strip().strip(":").replace("\\", "/")
    return ":" + ":".join(part for part in normalized.split("/") if part)


def find_android_module(project_dir: Path, preferred: str = "app") -> str:
    """Find an Android application module, even when the ZIP uses nested modules."""
    preferred_path = project_dir / module_to_path(preferred)
    if preferred and preferred.lower() != "auto":
        preferred_build_files = (
            preferred_path / "build.gradle",
            preferred_path / "build.gradle.kts",
        )
        if any(path.is_file() for path in preferred_build_files):
            return preferred.strip().strip(":").replace("/", ":")

    candidates: list[tuple[int, str]] = []
    for build_file in project_dir.rglob("build.gradle*"):
        if not build_file.is_file() or "build" in build_file.parts:
            continue
        try:
            contents = build_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "com.android.application" not in contents:
            continue
        if re.search(
            r"""id\s*\(?\s*['"]com\.android\.application['"]\s*\)?[^\n}]*\bapply\s+false\b""",
            contents,
            re.IGNORECASE,
        ):
            continue
        relative_module = build_file.parent.relative_to(project_dir)
        module = ":".join(relative_module.parts)
        candidates.append((len(relative_module.parts), module))

    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1] != "app", item[1]))
        return candidates[0][1]

    raise BuildError(
        "Could not find an Android application module in the ZIP. "
        "Expected an app module with the com.android.application plugin."
    )


def validate_project(project_dir: Path) -> None:
    """Check that a directory looks like a Gradle Android project."""
    if not project_dir.exists():
        raise BuildError(f"Project directory does not exist: {project_dir}")
    if not project_dir.is_dir():
        raise BuildError(f"Project path is not a directory: {project_dir}")

    has_settings = any(
        (project_dir / filename).is_file()
        for filename in ("settings.gradle", "settings.gradle.kts")
    )
    if not has_settings:
        raise BuildError(
            f"Not an Android Gradle project: missing settings.gradle(.kts) in {project_dir}"
        )

    if not find_gradle_executable(project_dir) and shutil.which("gradle") is None:
        raise BuildError(
            f"Gradle was not found in {project_dir}. Include gradlew in the ZIP "
            "or install Gradle on the build server."
        )


def find_gradle_executable(project_dir: Path) -> Path | None:
    """Return the platform-appropriate Gradle wrapper if one exists."""
    candidates = ("gradlew.bat", "gradlew") if os.name == "nt" else ("gradlew",)
    for filename in candidates:
        executable = project_dir / filename
        if executable.is_file():
            return executable
    return None


def gradle_command(
    project_dir: Path,
    task: str,
    *,
    module: str,
    extra_args: Sequence[str] = (),
) -> tuple[str, ...]:
    """Construct a safe, argument-list Gradle invocation."""
    wrapper = find_gradle_executable(project_dir)
    if wrapper is None and shutil.which("gradle") is None:
        raise BuildError(
            f"Gradle was not found in {project_dir}; expected gradlew or a "
            "system Gradle installation."
        )

    if wrapper is None:
        wrapper_command = ("gradle",)
    else:
        wrapper_command = (str(wrapper),) if os.name == "nt" else ("./gradlew",)
    if task.startswith(":"):
        task_name = task
    else:
        module_path = module_to_gradle_path(module)
        task_name = f":{task}" if module_path == ":" else f"{module_path}:{task}"
    return (*wrapper_command, task_name, *extra_args)


def run_gradle(
    project_dir: Path,
    command: Sequence[str],
    *,
    quiet: bool = False,
) -> None:
    """Run Gradle from the project directory and surface useful failures."""
    try:
        completed = subprocess.run(
            list(command),
            cwd=project_dir,
            check=False,
            text=True,
            stdout=subprocess.PIPE if quiet else None,
            stderr=subprocess.PIPE if quiet else None,
        )
    except OSError as exc:
        raise BuildError(f"Could not start Gradle: {exc}") from exc

    if completed.returncode != 0:
        details = ""
        if quiet:
            details = f"\n{completed.stdout}\n{completed.stderr}".strip()
        raise BuildError(
            f"Gradle failed with exit code {completed.returncode}"
            + (f":\n{details}" if details else ".")
        )


def find_apk(project_dir: Path, module: str, variant: str) -> Path:
    """Find the newest APK emitted for a module and variant."""
    output_dir = (
        project_dir
        / module_to_path(module)
        / "build"
        / "outputs"
        / "apk"
        / variant
    )
    if not output_dir.is_dir():
        raise BuildError(f"APK output directory was not created: {output_dir}")

    apks = [path for path in output_dir.glob("*.apk") if path.is_file()]
    if not apks:
        raise BuildError(f"No APK found in {output_dir}")
    return max(apks, key=lambda path: path.stat().st_mtime_ns)


def build_apk(
    project_dir: Path,
    *,
    module: str = "app",
    variant: str = "debug",
    output: Path | None = None,
    clean: bool = False,
    extra_args: Sequence[str] = (),
) -> BuildResult:
    """Assemble an Android APK and optionally copy it to a destination."""
    project_dir = project_dir.expanduser().resolve()
    validate_project(project_dir)

    if not variant or any(character in variant for character in "/\\"):
        raise BuildError("Variant must be a non-empty Gradle variant name.")
    if not module:
        raise BuildError("Module must be a non-empty Gradle module name.")

    module = find_android_module(project_dir, module)
    from .android_sdk import ensure_android_sdk

    ensure_android_sdk(project_dir)

    if clean:
        run_gradle(
            project_dir,
            gradle_command(project_dir, "clean", module=module),
        )

    task = f"assemble{variant[0].upper()}{variant[1:]}"
    command = gradle_command(
        project_dir,
        task,
        module=module,
        extra_args=extra_args,
    )
    run_gradle(project_dir, command)
    apk_path = find_apk(project_dir, module, variant)

    if output is not None:
        destination = output.expanduser()
        if not destination.is_absolute():
            destination = Path.cwd() / destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(apk_path, destination)
        apk_path = destination.resolve()

    return BuildResult(apk_path=apk_path, command=command)


def clean_project(project_dir: Path, *, module: str = "app") -> None:
    """Run the Gradle clean task for an Android project."""
    project_dir = project_dir.expanduser().resolve()
    validate_project(project_dir)
    run_gradle(project_dir, gradle_command(project_dir, "clean", module=module))