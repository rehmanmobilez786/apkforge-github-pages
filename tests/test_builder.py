import tempfile
import unittest
import os
from pathlib import Path

from apk_builder.builder import (
    BuildError,
    find_android_module,
    find_apk,
    gradle_command,
    module_to_gradle_path,
    module_to_path,
    validate_project,
)


class BuilderTests(unittest.TestCase):
    def make_project(self) -> Path:
        project = Path(tempfile.mkdtemp())
        (project / "settings.gradle").write_text("rootProject.name = 'demo'\n")
        (project / "gradlew").write_text("#!/bin/sh\n")
        return project

    def test_gradle_command_uses_module_and_variant(self) -> None:
        project = self.make_project()
        command = gradle_command(
            project,
            "assembleDebug",
            module="app",
            extra_args=("--stacktrace",),
        )
        self.assertEqual(command, ("./gradlew", ":app:assembleDebug", "--stacktrace"))

    def test_nested_module_paths_are_normalized(self) -> None:
        self.assertEqual(module_to_path(":mobile:app"), Path("mobile/app"))
        self.assertEqual(module_to_gradle_path("mobile/app"), ":mobile:app")

    def test_root_application_module_uses_root_gradle_task(self) -> None:
        project = self.make_project()
        command = gradle_command(project, "assembleDebug", module="")
        self.assertEqual(command, ("./gradlew", ":assembleDebug"))

    def test_auto_finds_android_application_module(self) -> None:
        project = self.make_project()
        (project / "build.gradle").write_text(
            "plugins { id 'com.android.application' version '8.1.4' apply false }\n"
        )
        module = project / "mobile" / "app"
        module.mkdir(parents=True)
        (module / "build.gradle").write_text(
            "plugins { id 'com.android.application' }\n"
        )
        self.assertEqual(find_android_module(project, "auto"), "mobile:app")

    def test_auto_finds_root_application_module(self) -> None:
        project = self.make_project()
        (project / "build.gradle").write_text(
            "plugins { id 'com.android.application' }\n"
        )
        self.assertEqual(find_android_module(project, "auto"), "")

    def test_validate_project_rejects_missing_wrapper(self) -> None:
        project = Path(tempfile.mkdtemp())
        (project / "settings.gradle").touch()
        with self.assertRaisesRegex(BuildError, "Gradle was not found"):
            validate_project(project)

    def test_find_apk_returns_newest_apk(self) -> None:
        project = self.make_project()
        output = project / "app/build/outputs/apk/debug"
        output.mkdir(parents=True)
        old_apk = output / "old.apk"
        new_apk = output / "new.apk"
        old_apk.write_bytes(b"old")
        new_apk.write_bytes(b"new")
        os.utime(old_apk, ns=(1, 1))
        os.utime(new_apk, ns=(2, 2))
        self.assertEqual(find_apk(project, "app", "debug"), new_apk)


if __name__ == "__main__":
    unittest.main()