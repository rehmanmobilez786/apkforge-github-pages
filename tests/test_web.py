import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from apk_builder.web import _extract_zip_safely, create_app


class WebTests(unittest.TestCase):
    def test_health_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = create_app(Path(temp_dir)).test_client()
            response = client.get("/healthz")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["status"], "APK Builder Online")

    def test_build_requires_zip_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = create_app(Path(temp_dir)).test_client()
            response = client.post("/build")
            self.assertEqual(response.status_code, 400)
            self.assertIn("ZIP", response.json["error"])

    def test_build_rejects_invalid_repository_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = create_app(Path(temp_dir)).test_client()
            response = client.post("/build", data={"source_url": "https://example.com/demo"})
            self.assertEqual(response.status_code, 400)
            self.assertIn("public GitHub", response.json["error"])

    def test_zip_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "unsafe.zip"
            destination = root / "source"
            destination.mkdir()
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("../outside.txt", "unsafe")
            with self.assertRaisesRegex(ValueError, "unsafe path"):
                _extract_zip_safely(
                    archive,
                    destination,
                    max_members=10,
                    max_extracted_bytes=100,
                )
            self.assertFalse((root / "outside.txt").exists())

    def test_corrupt_zip_returns_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            client = create_app(root).test_client()
            response = client.post(
                "/build",
                data={
                    "file": (
                        io.BytesIO(b"this is not a complete zip archive"),
                        "project.zip",
                    )
                },
                content_type="multipart/form-data",
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json["code"], "invalid_zip")
            self.assertIn("damaged or incomplete", response.json["error"])
            self.assertNotIn("Bad offset", response.json["error"])

    def test_download_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = create_app(Path(temp_dir)).test_client()
            response = client.get("/download/not-a-build/../secret.apk")
            self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()