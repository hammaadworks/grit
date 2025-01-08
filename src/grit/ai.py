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
        "temperature": 0.1,
        "max_tokens": 500
    }

    try:
        url = f"{base_url.rstrip('/')}/chat/completions"
        # Increased timeout to 60.0s to allow for local model cold-starts
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                message = choice.get("message", {})
                msg = message.get("content", "")
                
                # Fallback for models that output primarily in reasoning (common in some distilled models)
                if not msg.strip() and "reasoning" in message:
                    msg = message["reasoning"]
                
                msg = msg.strip()
                if not msg:
                    return None

                # Strip markdown code blocks just in case the LLM disobeys
                if msg.startswith("```"):
                    lines = msg.split("\n")
                    if len(lines) > 2:
                        msg = "\n".join(lines[1:-1])
                return msg
    except Exception as e:
        # Import internally to avoid circular dependencies
        from grit.ui import err_console, ERROR_COLOR
        err_console.print(f"\n    [{ERROR_COLOR}]AI Error: {str(e)}[/{ERROR_COLOR}]")
        return None
        
    return None
