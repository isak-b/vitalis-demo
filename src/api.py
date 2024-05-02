import os
from openai import OpenAI


def check_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        return False

    client = get_client()
    try:
        _ = client.completions.create(
            model="davinci-002",
            prompt="This is a test.",
            max_tokens=5
        )
    except Exception as e:
        return e
    else:
        return True


def get_client():
    """Configures and returns a chat client"""
    client = OpenAI()
    return client
