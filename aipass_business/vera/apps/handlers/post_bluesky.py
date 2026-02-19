"""Bluesky posting wrapper for AIPass Business."""

import os

from atproto import Client


def load_credentials():
    """Load Bluesky credentials from credentials file."""
    env_file = os.path.expanduser("~/.aipass/credentials/platform_keys.env")
    handle = None
    password = None
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("BLUESKY_HANDLE="):
                handle = line.split("=", 1)[1]
            elif line.startswith("BLUESKY_APP_PASSWORD="):
                password = line.split("=", 1)[1]
    if not handle or not password:
        raise RuntimeError("Bluesky credentials not found")
    return handle, password


def post(text):
    """Post to Bluesky. Returns the post URI."""
    handle, password = load_credentials()
    client = Client()
    client.login(handle, password)
    response = client.send_post(text=text)
    # Build web URL from response
    # URI format: at://did:plc:xxx/app.bsky.feed.post/rkey
    uri = response.uri
    rkey = uri.split("/")[-1]
    web_url = f"https://bsky.app/profile/{handle}/post/{rkey}"
    return web_url


if __name__ == "__main__":
    url = post("Testing Bluesky API integration from AIPass.")
    print(f"Posted: {url}")
