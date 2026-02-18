"""Dev.to posting wrapper for AIPass Business."""

import json
import os
import urllib.request


def load_api_key():
    """Load dev.to API key from credentials."""
    env_file = os.path.expanduser("~/.aipass/credentials/platform_keys.env")
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DEVTO_API_KEY="):
                return line.split("=", 1)[1]
    raise RuntimeError("DEVTO_API_KEY not found in credentials")


def post_article(title, body_markdown, tags=None, published=False):
    """Post an article to dev.to. Returns the article URL."""
    api_key = load_api_key()
    if tags is None:
        tags = []

    payload = {
        "article": {
            "title": title,
            "body_markdown": body_markdown,
            "tags": tags,
            "published": published,
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://dev.to/api/articles",
        data=data,
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
            "User-Agent": "AIPass/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("url", result.get("canonical_url", ""))


if __name__ == "__main__":
    url = post_article(
        title="AIPass: Test Post",
        body_markdown="Testing the dev.to API integration.",
        tags=["test"],
        published=False,
    )
    print(f"Posted: {url}")
