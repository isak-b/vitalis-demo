import os
from openai import OpenAI


def get_client(
    API_TYPE: str = None,
    OPENAI_API_KEY: str = None,
):
    """Configures and returns a chat client (e.g., openai=openai.OpenAI)"""
    if API_TYPE == "openai":
        client = OpenAI(
            api_key=OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"),
        )
    else:
        raise ValueError(f"{API_TYPE=} is not recognized")
    return client
