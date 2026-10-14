import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_article_length import measure


class ArticleLengthTests(unittest.TestCase):
    def test_markup_and_non_body_content_do_not_inflate_count(self):
        body = """# 長い記事タイトル

※本記事には広告・PRが含まれます。

## 手順

あいう **えお** [かき](https://example.com/very-long-url)

![画像の説明](images/inline-01.png)

```text
コードは数えない
```

<!-- 管理用コメント -->

<https://example.com/another-long-url>

- くけ

### 補足

こさ
"""
        result = measure(body)
        self.assertEqual(result["body_characters"], 11)
        self.assertEqual(result["sections"][1]["characters"], 9)
        self.assertEqual(result["sections"][2]["characters"], 2)

    def test_html_counts_visible_text_but_not_script_or_attributes(self):
        body = '<div><p>あいう<a href="https://example.com/">えお</a></p><script>無視</script></div>\n'
        self.assertEqual(measure(body)["body_characters"], 5)

    def test_cli_fails_short_article_and_accepts_boundary(self):
        script = Path(__file__).resolve().parents[1] / "scripts/check_article_length.py"
        with tempfile.TemporaryDirectory() as directory:
            body = Path(directory) / "article-body.md"
            for length, expected in ((2000, 1), (4999, 1), (5000, 0)):
                body.write_text("# タイトル\n\n" + "あ" * length, encoding="utf-8")
                result = subprocess.run([sys.executable, str(script), str(body)], capture_output=True, text=True)
                self.assertEqual(result.returncode, expected)
                self.assertEqual(json.loads(result.stdout)["articles"][0]["body_characters"], length)

    def test_batch_does_not_use_combined_length(self):
        script = Path(__file__).resolve().parents[1] / "scripts/check_article_length.py"
        with tempfile.TemporaryDirectory() as directory:
            files = [Path(directory) / "one.md", Path(directory) / "two.md"]
            for file, length in zip(files, (2000, 3000)):
                file.write_text("あ" * length, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), *map(str, files)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertTrue(all(not item["passed"] for item in json.loads(result.stdout)["articles"]))


if __name__ == "__main__":
    unittest.main()
