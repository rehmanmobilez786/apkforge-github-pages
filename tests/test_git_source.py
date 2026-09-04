import unittest

from apk_builder.builder import BuildError
from apk_builder.git_source import validate_repository_url


class GitSourceTests(unittest.TestCase):
    def test_normalizes_supported_repository_urls(self) -> None:
        self.assertEqual(
            validate_repository_url("https://github.com/example/demo.git"),
            "https://github.com/example/demo",
        )

    def test_rejects_non_public_or_non_repository_urls(self) -> None:
        for url in (
            "http://github.com/example/demo",
            "https://example.com/example/demo",
            "https://github.com/example/demo/tree/main",
            "https://user:password@github.com/example/demo",
        ):
            with self.subTest(url=url):
                with self.assertRaises(BuildError):
                    validate_repository_url(url)


if __name__ == "__main__":
    unittest.main()