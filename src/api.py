from openai import OpenAI


def check_api_key(api_key: str):
    client = get_client(api_key=api_key)
    try:
        _ = client.completions.create(
            model="davinci-002",
            prompt="This is a test.",
            max_tokens=5
        )
    except Exception:
        return False
    return True


def get_client(api_key: str):
    """Configures and returns a chat client"""
    return OpenAI(api_key=api_key)
