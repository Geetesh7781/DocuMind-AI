"""LLM answer generation grounded strictly in retrieved context."""
from .config import settings

SYSTEM = (
    "You are DocuMind, a precise document assistant. Answer ONLY from the numbered "
    "context passages. Cite every claim with its passage number like [1] or [2][3]. "
    "If the context does not contain the answer, say you could not find it in the "
    "uploaded documents. Be concise and well structured."
)


def _prompt(question: str, hits: list[dict]) -> str:
    ctx = "\n\n".join(
        f"[{i}] ({h['filename']}, p.{h['page']})\n{h['text']}" for i, h in enumerate(hits, 1)
    )
    return f"Context:\n{ctx}\n\nQuestion: {question}"


def generate(question: str, hits: list[dict]) -> str:
    provider = settings.llm_provider.lower()
    if provider == "anthropic" and settings.anthropic_api_key:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        r = client.messages.create(
            model=settings.anthropic_model, max_tokens=900, system=SYSTEM,
            messages=[{"role": "user", "content": _prompt(question, hits)}],
        )
        return r.content[0].text
    if provider == "openai" and settings.openai_api_key:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        r = client.chat.completions.create(
            model=settings.openai_model, max_tokens=900,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": _prompt(question, hits)}],
        )
        return r.choices[0].message.content
    # Retrieval-only fallback so the app works without any API key.
    top = hits[0]
    return (f"(Retrieval-only mode: no LLM key configured.) Most relevant passage, "
            f"{top['filename']} p.{top['page']}: {top['text'][:500]}… [1]")
