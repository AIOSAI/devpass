"""Twitter/X posting wrapper for AIPass Business."""

import os

import tweepy


def load_credentials():
    """Load Twitter OAuth credentials from credentials file."""
    env_file = os.path.expanduser("~/.aipass/credentials/platform_keys.env")
    keys = {}
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            for prefix in [
                "TWITTER_CONSUMER_KEY",
                "TWITTER_CONSUMER_SECRET",
                "TWITTER_ACCESS_TOKEN",
                "TWITTER_ACCESS_TOKEN_SECRET",
            ]:
                if line.startswith(f"{prefix}="):
                    keys[prefix] = line.split("=", 1)[1]
    return keys


def post(text):
    """Post a tweet. Returns the tweet URL."""
    creds = load_credentials()
    client = tweepy.Client(
        consumer_key=creds["TWITTER_CONSUMER_KEY"],
        consumer_secret=creds["TWITTER_CONSUMER_SECRET"],
        access_token=creds["TWITTER_ACCESS_TOKEN"],
        access_token_secret=creds["TWITTER_ACCESS_TOKEN_SECRET"],
    )
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]  # type: ignore[union-attr]
    return f"https://x.com/AIPassSystem/status/{tweet_id}"


if __name__ == "__main__":
    url = post("Testing Twitter API integration from AIPass.")
    print(f"Posted: {url}")
