"""Refresh the static community section from official RSS feeds."""

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape, unescape
from pathlib import Path
import re
import sys
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


FEEDS = (
    ("Microsoft for Developers", "https://devblogs.microsoft.com/feed/"),
    ("The GitHub Blog", "https://github.blog/feed/"),
    ("Microsoft Foundry Blog", "https://devblogs.microsoft.com/foundry/feed/"),
)
START = "<!-- community-feed:start -->"
END = "<!-- community-feed:end -->"
PAGE = Path(__file__).resolve().parents[1] / "index.html"
MAX_ITEMS = 6
MAX_FEED_BYTES = 5_000_000


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    publisher: str
    published: datetime
    topics: tuple[str, ...]


def plain_text(value):
    return " ".join(unescape(re.sub(r"<[^>]*>", "", value)).split())


def topics_for(title, categories, feed_url):
    # Match editorial metadata, not article bodies or newsletter footers.
    text = " ".join((title, *categories)).casefold()
    github_copilot = bool(re.search(r"\bgithub[\s-]+copilot\b", text))
    foundry = bool(re.search(r"\b(?:microsoft|azure ai)[\s-]+foundry\b", text))
    m365 = bool(re.search(r"\b(?:m365|microsoft\s*365|office\s*365)\b", text))
    if m365 and not (github_copilot or foundry):
        return ()

    topics = []
    if github_copilot:
        topics.append("GitHub Copilot")
    if foundry or feed_url == FEEDS[2][1]:
        topics.append("Microsoft Foundry")
    if re.search(r"\b(?:vs\s*code|visual studio code)\b", text):
        topics.append("VS Code")
    if re.search(
        r"\b(?:coding agents?|agentic (?:development|coding)|agent (?:framework|toolkit|mode))\b",
        text,
    ) or ("agents" in categories and feed_url == FEEDS[1][1]):
        topics.append("Developer agents")
    if re.search(
        r"\b(?:developer tool(?:s|ing)|dev tools|dev\s*containers?|"
        r"github (?:actions|codespaces)|wsl|windows subsystem for linux)\b",
        text,
    ):
        topics.append("Developer tooling")
    return tuple(topics)


def canonical_url(value):
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or parts.netloc not in {"devblogs.microsoft.com", "github.blog"}
        or not parts.path.strip("/")
    ):
        raise ValueError(f"Unexpected article URL: {value!r}")
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


def parse_feed(content, publisher, feed_url):
    root = ET.fromstring(content)
    items = root.findall("./channel/item")
    if not items:
        raise ValueError(f"No RSS items in {feed_url}")
    articles = []
    for item in items:
        title = plain_text(item.findtext("title", ""))
        categories = tuple(
            plain_text(category.text or "").casefold()
            for category in item.findall("category")
        )
        topics = topics_for(title, categories, feed_url)
        if not topics:
            continue
        url = canonical_url((item.findtext("link") or "").strip())
        date = item.findtext("pubDate")
        if not title or not date:
            raise ValueError(f"Missing article metadata in {feed_url}")
        published = parsedate_to_datetime(date)
        if published.tzinfo is None:
            raise ValueError(f"Missing publication timezone: {title}")
        articles.append(
            Article(title, url, publisher, published.astimezone(timezone.utc), topics)
        )
    return articles


def select_articles(articles):
    unique = {}
    for article in sorted(articles, key=lambda a: a.published, reverse=True):
        unique.setdefault(article.url, article)
    return list(unique.values())[:MAX_ITEMS]


def render_feed(articles, updated):
    if not articles:
        raise ValueError("No matching community articles; keeping the existing page")
    stamp = updated.astimezone(timezone.utc)
    lines = [
        f'            <p class="community-updated">Feed refreshed: <time datetime="{stamp.isoformat()}">'
        f'{stamp:%b %d, %Y at %H:%M} UTC</time>. Checked daily; articles are ordered by publication date.</p>',
        '            <div class="community-grid">',
    ]
    for article in articles:
        date = article.published
        tags = " ".join(
            f'<span class="tag">{escape(topic)}</span>' for topic in article.topics
        )
        lines.extend((
            '              <article class="community-card">',
            f'                <div class="community-topics">{tags}</div>',
            f'                <h3><a href="{escape(article.url, quote=True)}" target="_blank" rel="noreferrer">'
            f'{escape(article.title)}</a></h3>',
            f'                <p>{escape(article.publisher)} &middot; '
            f'<time datetime="{date.date().isoformat()}">{date:%b %d, %Y}</time></p>',
            '              </article>',
        ))
    lines.append("            </div>")
    return "\n".join(lines)


def replace_feed(page, rendered):
    if page.count(START) != 1 or page.count(END) != 1:
        raise ValueError("Expected exactly one pair of community feed markers")
    before, remainder = page.split(START)
    _, after = remainder.split(END)
    return f"{before}{START}\n{rendered}\n            {END}{after}"


def main():
    articles = []
    for publisher, url in FEEDS:
        request = Request(url, headers={"User-Agent": "CA-Build-Guild-Community/1.0"})
        with urlopen(request, timeout=30) as response:
            content = response.read(MAX_FEED_BYTES + 1)
        if len(content) > MAX_FEED_BYTES:
            raise ValueError(f"RSS feed exceeds size limit: {url}")
        parsed = parse_feed(content, publisher, url)
        print(f"{publisher}: {len(parsed)} matching articles")
        articles.extend(parsed)

    selected = select_articles(articles)
    rendered = render_feed(selected, datetime.now(timezone.utc))
    page = PAGE.read_text(encoding="utf-8")
    updated = replace_feed(page, rendered)
    PAGE.write_text(updated, encoding="utf-8", newline="\n")
    print(f"Published {len(selected)} community cards to {PAGE.name}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, URLError, ET.ParseError, ValueError, TypeError) as error:
        print(f"Community feed refresh failed: {error}", file=sys.stderr)
        sys.exit(1)
