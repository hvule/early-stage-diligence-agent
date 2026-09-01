import os
from typing import Optional

from openai import OpenAI


#DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

def get_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Export it before running the program."
        )
    return OpenAI()


def call_llm(prompt: str, *, use_web: bool = False,
             model: Optional[str] = None,
             reasoning_effort: str = "medium") -> str:
    """
    General LLM call using the OpenAI Responses API.

    If use_web=True, the model is given the hosted web_search tool and is
    instructed by the caller's prompt on how to use sources.
    """
    client = get_client()

    kwargs = {
        "model": model or DEFAULT_MODEL,
        "input": prompt,
        "reasoning": {"effort": reasoning_effort},
    }

    if use_web:
        kwargs["tools"] = [{"type": "web_search"}]
        kwargs["tool_choice"] = "auto"
        # Retains the complete set of consulted web-search sources in the response.
        kwargs["include"] = ["web_search_call.action.sources"]

    response = client.responses.create(**kwargs)
    return response.output_text
