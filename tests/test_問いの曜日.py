import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import compose  # noqa: E402


class 問いの曜日のテスト(unittest.TestCase):
    def test_火金は言葉(self):
        for d in (date(2026, 11, 24), date(2026, 11, 27)):
            self.assertIn("土地の言葉 × 県外", compose.問いの題材の指示(d)[0])

    def test_ほかは暮らし(self):
        for d in (date(2026, 11, 23), date(2026, 11, 25), date(2026, 11, 29)):
            文 = compose.問いの題材の指示(d)[0]
            self.assertIn("暮らし × 県外", 文)
            self.assertIn("土地の言葉を聞かない", 文)


if __name__ == "__main__":
    unittest.main()
