"""Command-line interface for apk-builder."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .builder import BuildError, build_apk, clean_project, find_apk


def _add_project_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "project",
        type=Path,
        help="Path to the Android Gradle project",
    )
    parser.add_argument(
        "--module",
        default="app",
        help="Gradle module containing the Android app (default: app)",
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apk-builder",
        description="Build and collect APKs from Android Gradle projects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Assemble an APK")
    _add_project_options(build)
    build.add_argument(
        "--variant",
        default="debug",
        help="Build variant to assemble (default: debug)",
    )
    build.add_argument(
        "--output",
        type=Path,
        help="Destination file for the APK",
    )
    build.add_argument(
        "--clean",
        action="store_true",
        help="Run Gradle clean before assembling",
    )
    build.add_argument(
        "--gradle-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="Additional argument passed to Gradle; repeat for multiple arguments",
    )

    clean = subparsers.add_parser("clean", help="Run Gradle clean")
    _add_project_options(clean)

    locate = subparsers.add_parser(
        "locate",
        help="Locate an APK that was already built",
    )
    _add_project_options(locate)
    locate.add_argument(
        "--variant",
        default="debug",
        help="Build variant to inspect (default: debug)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_apk(
                args.project,
                module=args.module,
                variant=args.variant,
                output=args.output,
                clean=args.clean,
                extra_args=args.gradle_arg,
            )
            print(f"APK ready: {result.apk_path}")
        elif args.command == "clean":
            clean_project(args.project, module=args.module)
            print("Gradle clean completed.")
        else:
            apk = find_apk(
                args.project.expanduser().resolve(),
                args.module,
                args.variant,
            )
            print(apk)
    except BuildError as exc:
        print(f"apk-builder: error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())