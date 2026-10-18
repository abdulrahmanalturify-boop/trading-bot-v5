"""The date and photo read from an article page's head (newspics.published_in / image_in), no network.

Run: python -m unittest discover -s tests -p 'test_newspics.py' -v
"""
import unittest

import pandas as pd

import newspics as NP

HEAD = ('<head><meta property="og:title" content="x"><meta property="article:published_time" content="2026-10-11T09:30:00+03:00">'
        '<meta property="og:image" content="//cdn.example.com/a/photo.jpg"></head>')
JSON_LD = '<head><script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-10-11T06:30:00Z"}</script></head>'


class PageHead(unittest.TestCase):
    def test_meta_date_in_utc(self):
        self.assertEqual(NP.published_in(HEAD), pd.Timestamp("2026-10-11T06:30:00Z"))

    def test_json_ld_date(self):
        self.assertEqual(NP.published_in(JSON_LD), pd.Timestamp("2026-10-11T06:30:00Z"))

    def test_day_in_the_address(self):
        self.assertEqual(NP.published_in("<head></head>", "https://www.example.com/2026/10/11/some-story/"),
                         pd.Timestamp("2026-10-11T12:00:00Z"))
        self.assertIsNone(NP.published_in("<head></head>", "https://www.example.com/story/12345"))

    def test_absurd_dates_are_ignored(self):
        self.assertIsNone(NP.published_in('<head><meta name="date" content="1970-01-01"></head>'))
        self.assertIsNone(NP.published_in('<head><meta name="date" content="next week"></head>'))

    def test_photo(self):
        self.assertEqual(NP.image_in(HEAD, "https://www.example.com/x"), "https://cdn.example.com/a/photo.jpg")
        self.assertEqual(NP.image_in('<head><meta property="og:image" content="/img/logo.png"></head>', "https://e.com/"), "")


if __name__ == "__main__":
    unittest.main()
