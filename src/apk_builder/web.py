"""Flask API for uploading Android projects and downloading built APKs.

Only run this service with trusted uploads. Gradle projects execute their own
build scripts, so this service is not a sandbox for arbitrary internet users.
"""

from __future__ import annotations

import os
import shutil
import uuid
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename

from .builder import BuildError, build_apk, find_gradle_executable
from .git_source import clone_repository

DEFAULT_UPLOAD_FOLDER = Path("/tmp/apk-builds")
DEFAULT_MAX_UPLOAD_BYTES = 200 * 1024 * 1024
MAX_ZIP_MEMBERS = 5_000
MAX_EXTRACTED_BYTES = 750 * 1024 * 1024


def _configured_upload_folder() -> Path:
    configured = os.environ.get("APK_BUILDER_UPLOAD_FOLDER")
    return Path(configured).expanduser() if configured else DEFAULT_UPLOAD_FOLDER


def _configured_max_upload_bytes() -> int:
    configured = os.environ.get("APK_BUILDER_MAX_UPLOAD_BYTES")
    if not configured:
        return DEFAULT_MAX_UPLOAD_BYTES
    try:
        value = int(configured)
    except ValueError as exc:
        raise ValueError("APK_BUILDER_MAX_UPLOAD_BYTES must be an integer") from exc
    if value <= 0:
        raise ValueError("APK_BUILDER_MAX_UPLOAD_BYTES must be positive")
    return value


def create_app(upload_folder: Path | None = None) -> Flask:
    """Create the APK builder Flask application."""
    app = Flask(__name__)
    base_path = os.environ.get("BASE_PATH", "").rstrip("/")
    route = lambda path: f"{base_path}{path}" or "/"
    app.config["UPLOAD_FOLDER"] = Path(
        upload_folder or _configured_upload_folder()
    ).expanduser().resolve()
    app.config["MAX_CONTENT_LENGTH"] = _configured_max_upload_bytes()
    app.config["JSON_SORT_KEYS"] = False
    app.config["JSON_AS_ASCII"] = False
    app.config["MAX_EXTRACTED_BYTES"] = MAX_EXTRACTED_BYTES
    app.config["MAX_ZIP_MEMBERS"] = MAX_ZIP_MEMBERS
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)

    @app.errorhandler(413)
    def request_too_large(_error: object):
        return (
            jsonify(
                {
                    "status": "Build failed",
                    "error": "Uploaded ZIP is too large.",
                }
            ),
            413,
        )

    @app.get(route("/"))
    @app.get(route("/healthz"))
    def health():
        return jsonify({"status": "APK Builder Online"})

    @app.post(route("/build"))
    def build_uploaded_project():
        upload = request.files.get("file")
        source_url = request.form.get("source_url", "").strip()
        has_upload = upload is not None and bool(upload.filename)
        if not has_upload and not source_url:
            return jsonify({"error": "No ZIP file or repository URL was provided."}), 400
        if has_upload and source_url:
            return jsonify({"error": "Choose either a ZIP file or a repository URL, not both."}), 400

        original_name = secure_filename(upload.filename) if has_upload else ""
        if has_upload and not original_name.lower().endswith(".zip"):
            return jsonify({"error": "Only ZIP files are supported."}), 400

        module = request.form.get("module", "auto").strip()
        variant = request.form.get("variant", "release").strip()
        if not module or not variant:
            return jsonify({"error": "Module and variant must not be empty."}), 400

        build_id = uuid.uuid4().hex
        build_dir = app.config["UPLOAD_FOLDER"] / f"build_{build_id}"
        archive_path: Path | None = (
            build_dir / (original_name or "project.zip") if has_upload else None
        )
        source_dir = build_dir / "source"
        apk_dir = build_dir / "apk"

        try:
            build_dir.mkdir(parents=True)
            source_dir.mkdir()
            apk_dir.mkdir()
            if source_url:
                clone_repository(source_url, source_dir)
            else:
                assert upload is not None and archive_path is not None
                upload.save(archive_path)
                _extract_zip_safely(
                    archive_path,
                    source_dir,
                    max_members=app.config["MAX_ZIP_MEMBERS"],
                    max_extracted_bytes=app.config["MAX_EXTRACTED_BYTES"],
                )
            project_dir = _find_project_root(source_dir)
            _make_wrapper_executable(project_dir)
            result = build_apk(
                project_dir,
                module=module,
                variant=variant,
                output=apk_dir / f"{module.replace(':', '_')}-{variant}.apk",
            )
        except zipfile.BadZipFile:
            shutil.rmtree(build_dir, ignore_errors=True)
            return (
                jsonify(
                    {
                        "status": "Build failed",
                        "code": "invalid_zip",
                        "error": (
                            "The uploaded ZIP file is damaged or incomplete. "
                            "Please create a new ZIP, wait for it to finish saving, "
                            "and upload it again. Password-protected ZIP files are "
                            "not supported."
                        ),
                    }
                ),
                400,
            )
        except (BuildError, OSError, ValueError) as exc:
            shutil.rmtree(build_dir, ignore_errors=True)
            return jsonify({"status": "Build failed", "error": str(exc)}), 400
        finally:
            if archive_path is not None:
                archive_path.unlink(missing_ok=True)

        filename = result.apk_path.name
        return jsonify(
            {
                "status": "APK ready",
                "build_id": build_id,
                "filename": filename,
                "download_url": f"{base_path}/download/{build_id}/{filename}",
            }
        )

    @app.get(route("/download/<build_id>/<filename>"))
    def download_apk(build_id: str, filename: str):
        if not _is_build_id(build_id):
            return jsonify({"error": "Build was not found."}), 404

        safe_filename = secure_filename(filename)
        if safe_filename != filename or not safe_filename.lower().endswith(".apk"):
            return jsonify({"error": "APK was not found."}), 404

        apk_path = (
            app.config["UPLOAD_FOLDER"]
            / f"build_{build_id}"
            / "apk"
            / safe_filename
        )
        if not apk_path.is_file():
            return jsonify({"error": "APK was not found."}), 404
        return send_file(
            apk_path,
            mimetype="application/vnd.android.package-archive",
            as_attachment=True,
            download_name=safe_filename,
        )

    return app


def _extract_zip_safely(
    archive_path: Path,
    destination: Path,
    *,
    max_members: int,
    max_extracted_bytes: int,
) -> None:
    """Extract a ZIP only when every member stays inside destination."""
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > max_members:
            raise ValueError("ZIP contains too many files.")

        total_size = sum(member.file_size for member in members)
        if total_size > max_extracted_bytes:
            raise ValueError("ZIP expands beyond the allowed size.")

        destination_root = destination.resolve()
        for member in members:
            member_path = (destination / member.filename).resolve()
            try:
                member_path.relative_to(destination_root)
            except ValueError as exc:
                raise ValueError("ZIP contains an unsafe path.") from exc

            if _zip_member_is_symlink(member):
                raise ValueError("ZIP contains an unsupported symbolic link.")

        archive.extractall(destination)


def _zip_member_is_symlink(member: zipfile.ZipInfo) -> bool:
    """Return whether a ZIP member declares a Unix symbolic link."""
    unix_mode = (member.external_attr >> 16) & 0o170000
    return unix_mode == 0o120000


def _find_project_root(source_dir: Path) -> Path:
    """Find the Gradle root anywhere in the uploaded ZIP tree."""
    candidates = [source_dir]
    candidates.extend(path for path in source_dir.rglob("*") if path.is_dir())
    project_candidates: list[tuple[int, int, Path]] = []
    for candidate in candidates:
        has_settings = any(
            (candidate / name).is_file()
            for name in ("settings.gradle", "settings.gradle.kts")
        )
        has_gradle = find_gradle_executable(candidate) is not None
        if has_settings and (has_gradle or shutil.which("gradle") is not None):
            # Prefer the shallowest root, then a project that includes its wrapper.
            depth = len(candidate.relative_to(source_dir).parts)
            project_candidates.append((depth, 0 if has_gradle else 1, candidate))

    if project_candidates:
        project_candidates.sort(key=lambda item: (item[0], item[1]))
        return project_candidates[0][2]

    raise BuildError(
        "Could not find an Android Gradle project in the source. The ZIP or "
        "repository must contain settings.gradle(.kts), plus gradlew or a server "
        "Gradle installation."
    )


def _make_wrapper_executable(project_dir: Path) -> None:
    wrapper = project_dir / "gradlew"
    if wrapper.is_file() and os.name != "nt":
        wrapper.chmod(wrapper.stat().st_mode | 0o111)


def _is_build_id(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return len(value) == 32


def main() -> None:
    """Run the development server."""
    port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "0.0.0.0")
    create_app().run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()