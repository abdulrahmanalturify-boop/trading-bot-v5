"""Regression checks for X platform branding; stdlib-only to run in CI."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class XBrandTests(unittest.TestCase):
    def read(self, file):
        return (ROOT / file).read_text(encoding="utf-8")

    def test_all_project_python_files_compile(self):
        for f in ROOT.rglob("*.py"):
            if ".git" not in f.parts:
                with self.subTest(path=str(f.relative_to(ROOT))):
                    compile(f.read_text(encoding="utf-8"), str(f), "exec")

    def test_logo_is_shared_for_html_and_native_page_links(self):
        theme = self.read("theme.py")
        app = self.read("app.py")
        self.assertIn("def xlogo(", theme)
        self.assertIn("XLOGO_D = ", theme)
        self.assertIn("def xify(", theme)
        self.assertIn("_XLOGO_MASK", theme)
        self.assertIn('a[href$="x-bots"]', theme)
        self.assertIn("T.X_BRAND_CSS", app)
        self.assertIn("st-key-alturaifi_ai_xbrand_", theme)
        self.assertIn("alturaifi_ai_xbrand_", self.read("ai_assistant.py"))
        self.assertIn('if k == "xbots" else page.title', app)
        self.assertIn('if k == "xbots" else P[k].title', app)

    def test_page_and_cards_use_brand_svg_not_at_symbol(self):
        page = self.read("p_xbots.py")
        overview = self.read("p_overview.py")
        promo = self.read("promo.py")
        self.assertIn('{T.xlogo()}{T.xify(head)}', page)
        self.assertIn('{T.xlogo()}<i></i><span>{T.xify(head)}', page)
        self.assertIn('{T.xlogo()}{T.esc(L("Open post", "افتح المنشور"))}', page)
        self.assertIn('T.xlogo() if key == "xbots"', overview)
        self.assertIn('T.xlogo() if key == "xbots"', promo)
        self.assertNotIn('T.icon("alternate_email")', page)
        self.assertNotIn('X (Twitter)', page)
        self.assertNotIn('X (تويتر)', page)

    def test_plain_x_is_not_globally_modified(self):
        theme = self.read("theme.py")
        self.assertIn("def xify(text):", theme)
        self.assertIn("return _XTOK.sub(", theme)
        # The normal esc() utility remains an ordinary HTML-escape function.
        self.assertIn("return html.escape(str(s))", theme)


if __name__ == "__main__":
    unittest.main()
