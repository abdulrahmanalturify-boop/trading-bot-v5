"""Every module that carries BUILD is in app.py's reload list, so the server's in-place update (no restart) reloads it:
mascot.py was missing and the AI button kept its old name after an update."""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ReloadOrderTest(unittest.TestCase):
    def test_every_versioned_module_reloads(self):
        src = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
        order = set(re.findall(r'"(\w+)"', re.search(r"_ORDER = \[(.*?)\]", src, re.S).group(1)))
        versioned = {os.path.basename(f)[:-3] for f in glob.glob(os.path.join(ROOT, "*.py"))
                     if re.search(r'^BUILD = "', open(f, encoding="utf-8").read(), re.M)} - {"app"}
        self.assertEqual(versioned - order, set())


if __name__ == "__main__":
    unittest.main()
