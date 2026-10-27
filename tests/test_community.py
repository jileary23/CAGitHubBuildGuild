from datetime import datetime, timezone
from html import escape
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import URLError
import xml.etree.ElementTree as ET

from scripts.update_community import (
    Article, END, FEEDS, START, canonical_url, main, parse_feed, render_feed,
    replace_feed, select_articles, topics_for,
)


class CommunityTests(unittest.TestCase):
    def test_topics(self):
        cases = (
            ("GitHub Copilot CLI updates", (), FEEDS[1][1], "GitHub Copilot"),
            ("GitHub-Copilot routing", (), FEEDS[0][1], "GitHub Copilot"),
            ("New Copilot features", (), FEEDS[0][1], None),
            ("Microsoft 365 Copilot agents in VS Code", (), FEEDS[0][1], None),
            ("M365 Copilot developer tools", (), FEEDS[0][1], None),
            ("Office 365 Copilot agent framework", (), FEEDS[1][1], None),
            ("Copilot agents", ("microsoft 365", "agents"), FEEDS[1][1], None),
            ("GitHub Copilot vs Microsoft 365 Copilot", (), FEEDS[1][1], "GitHub Copilot"),
            ("Microsoft Foundry tools", (), FEEDS[0][1], "Microsoft Foundry"),
            ("Azure AI Foundry tools", (), FEEDS[0][1], "Microsoft Foundry"),
            ("New model releases", (), FEEDS[2][1], "Microsoft Foundry"),
            ("M365 Copilot agents", (), FEEDS[2][1], None),
            ("PostgreSQL in VS Code", (), FEEDS[0][1], "VS Code"),
            ("Visual Studio Code tips", (), FEEDS[0][1], "VS Code"),
            ("New coding agents", (), FEEDS[0][1], "Developer agents"),
            ("Agent updates", ("agents",), FEEDS[1][1], "Developer agents"),
            ("GitHub Actions improvements", (), FEEDS[1][1], "Developer tooling"),
            ("WSL containers", (), FEEDS[0][1], "Developer tooling"),
            ("Unrelated news", (), FEEDS[0][1], None),
        )
        for title, categories, feed, expected in cases:
            with self.subTest(title=title):
                topics = topics_for(title, categories, feed)
                if expected is None:
                    self.assertEqual(topics, ())
                else:
                    self.assertIn(expected, topics)

    def rss(self, title="GitHub Copilot update", url="https://github.blog/news/test/",
            date="Mon, 26 Oct 2026 15:05:12 +0000"):
        return (
            f"<rss><channel><item><title>{escape(title)}</title>"
            f"<link>{escape(url)}</link><pubDate>{date}</pubDate>"
            "<category>GitHub Copilot</category></item></channel></rss>"
        )

    def test_parse_feed(self):
        article, = parse_feed(self.rss(), *FEEDS[1])
        self.assertEqual(article.url, "https://github.blog/news/test")
        self.assertEqual(article.published.tzinfo, timezone.utc)
        self.assertEqual(article.topics, ("GitHub Copilot",))

    def test_invalid_feeds_and_metadata_fail(self):
        for content in (
            "not xml", "<rss><channel/></rss>", self.rss(date="invalid"),
            self.rss(date="Mon, 26 Oct 2026 15:05:12"),
            self.rss(url="javascript:alert(1)"),
        ):
            with self.subTest(content=content), self.assertRaises((ET.ParseError, ValueError)):
                parse_feed(content, *FEEDS[1])

    def test_article_body_is_not_used_for_topic_matching(self):
        content = (
            "<rss><channel><item><title>Unrelated news</title>"
            "<description>Footer: try GitHub Copilot</description>"
            "</item></channel></rss>"
        )
        self.assertEqual(parse_feed(content, *FEEDS[0]), [])

    def test_failed_fetch_preserves_snapshot(self):
        with TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            original = f"before{START}existing cards{END}after"
            page.write_text(original, encoding="utf-8")
            with (
                patch("scripts.update_community.PAGE", page),
                patch("scripts.update_community.urlopen", side_effect=[
                    BytesIO(self.rss().encode()), URLError("Feed unavailable"),
                ]),
                self.assertRaises(URLError),
            ):
                main()
            self.assertEqual(page.read_text(encoding="utf-8"), original)

    def test_only_allow_official_https_article_links(self):
        for url in (
            "http://github.blog/news", "https://github.blog.evil.test/news",
            "https://github.blog@evil.test/news", "https://example.com/news",
            "https://github.blog/",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_url(url)
        self.assertEqual(
            canonical_url("https://github.blog/news/?utm_source=rss#section"),
            "https://github.blog/news",
        )

    def article(self, number, title="GitHub Copilot update"):
        return Article(
            title, f"https://github.blog/news/{number}", "The GitHub Blog",
            datetime(2026, 10, number, tzinfo=timezone.utc), ("GitHub Copilot",),
        )

    def test_deduplicate_order_and_limit(self):
        articles = [self.article(n) for n in range(1, 10)]
        selected = select_articles([*articles, articles[-1]])
        self.assertEqual(len(selected), 6)
        self.assertEqual([a.published.day for a in selected], [9, 8, 7, 6, 5, 4])

    def test_render_escapes_text_and_includes_dates(self):
        rendered = render_feed(
            [self.article(1, 'Copilot & <script>alert("x")</script>')],
            datetime(2026, 10, 27, tzinfo=timezone.utc),
        )
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn('datetime="2026-10-01"', rendered)
        self.assertIn('datetime="2026-10-27T00:00:00+00:00"', rendered)
        self.assertIn('rel="noreferrer"', rendered)

    def test_empty_refresh_does_not_replace_content(self):
        with self.assertRaises(ValueError):
            render_feed([], datetime.now(timezone.utc))

    def test_replace_only_feed_region(self):
        original = f"before{START}\nold cards\n{END}after"
        updated = replace_feed(original, "new cards")
        self.assertEqual(updated, f"before{START}\nnew cards\n            {END}after")
        for invalid in ("no markers", START, END, START + END + START):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                replace_feed(invalid, "new cards")


if __name__ == "__main__":
    unittest.main()
