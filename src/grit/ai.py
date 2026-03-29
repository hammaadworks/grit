import httpx
import json
from typing import Optional

def generate_commit_message(diff: str, base_url: str, api_key: str, model: str) -> Optional[str]:
    """
    Calls an LLM endpoint (Ollama, Claude, OpenAI, etc.) to generate a perfect Conventional Commit message.
    """
    if not api_key or not base_url or not diff.strip():
        return None

    # We enforce a strict system prompt for high-quality DevX output
    system_prompt = (
        "You are an expert principal software engineer. Generate a perfectly formatted Conventional "
        "Commit message based on the provided git diff. Do NOT wrap it in quotes, code blocks, or "
        "add any explanation. Follow this strict format:\n"
        "<type>(<scope>): <subject>\n\n"
        "<body>\n\n"
        "Rules:\n"
        "- Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert\n"
        "- Scope is optional but highly recommended if obvious.\n"
        "- Subject MUST be imperative, present tense: 'change' not 'changed' nor 'changes'.\n"
        "- Max subject length: 50 characters.\n"
        "- Only output the raw commit message."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Format standard LLM payload (Supported by Ollama, Anthropic/Claude, OpenAI, etc.)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the diff:\n\n{diff}"}
        ],
        "temperature": 0.3,
        "max_tokens": 200
    }

    try:
        url = f"{base_url.rstrip('/')}/chat/completions"
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0]["message"]["content"].strip()
                # Strip markdown code blocks just in case the LLM disobeys
                if msg.startswith("```"):
                    msg = "\n".join(msg.split("\n")[1:-1])
                return msg
    except Exception as e:
        return None
        
    return None
