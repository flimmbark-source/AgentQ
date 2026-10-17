import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from validate_changes import validate_file, parse_porcelain


class ValidationTests(unittest.TestCase):
    def test_porcelain_file_list(self):
        self.assertEqual(parse_porcelain(b"?? prototypes/foo/index.html\x00 M prototypes/foo/README.md\x00"), ["prototypes/foo/index.html", "prototypes/foo/README.md"])

    def test_denies_deletion_and_rename(self):
        for status in (b" D ", b"R  ", b"UU "):
            with self.assertRaises(ValueError):
                parse_porcelain(status + b"prototypes/x.txt\x00")

    def test_denies_out_of_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "AGENTS.md"
            p.write_text("test")
            with self.assertRaisesRegex(ValueError, "Outside task allowlist"):
                validate_file(Path(folder), "AGENTS.md", ["prototypes/example/"])

    def test_passes_safe_output(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "prototypes" / "example" / "index.html"
            p.parent.mkdir(parents=True)
            p.write_text("<p>Demo</p>")
            self.assertGreater(validate_file(Path(folder), "prototypes/example/index.html", ["prototypes/example/"]), 0)

    def test_denies_secret_like_content(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "prototypes" / "example" / "test.txt"
            p.parent.mkdir(parents=True)
            p.write_text("-----BEGIN PRIVATE KEY-----")
            with self.assertRaisesRegex(ValueError, "Credential-looking"):
                validate_file(Path(folder), "prototypes/example/test.txt", ["prototypes/example/"])


if __name__ == "__main__":
    unittest.main()
