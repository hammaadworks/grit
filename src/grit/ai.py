import httpx
import json
from typing import Optional

def generate_commit_message(diff: str, base_url: str, api_key: str, model: str, verbose: bool = False) -> Optional[str]:
    """
    Calls an LLM endpoint (Ollama, Claude, OpenAI, etc.) to generate a perfect Conventional Commit message.
    """
    if not api_key or not base_url or not diff.strip():
        return None

    # Command-style prompt engineered for maximum precision on small/distilled models.
    system_prompt = (
        "TASK: Generate a professional Git Commit message in Conventional Commits format.\n"
        "INPUT: A git diff of changes.\n"
        "OUTPUT: ONLY the commit message. NO conversation. NO preamble. NO 'Here is the message'.\n\n"
        "FORMAT RULES:\n"
        "1. Header: <type>(<scope>): <subject>\n"
        "2. Types: feat, fix, refactor, docs, style, test, chore, perf, build, ci.\n"
        "3. Subject: Imperative ('add' not 'added'), present tense, max 50 chars, no period.\n"
        "4. Body: Leave one blank line after header. Explain 'why' and 'what', not 'how'.\n\n"
        "EXAMPLES:\n"
        "feat(auth): add JWT refresh token support\n\n"
        "Implemented a rotating refresh token strategy to improve session security\n"
        "without forcing frequent re-logins.\n\n"
        "fix(api): handle null pointer in user profile lookup\n\n"
        "Resolved a crash occurring when fetching profiles for deactivated users\n"
        "by adding a non-null guard in the repository layer.\n\n"
        "STRICT: If you output anything other than the raw commit message, the system will fail."
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

    if verbose:
        from grit.ui import console, BRAND_COLOR
        console.print(f"\n[bold {BRAND_COLOR}]--- AI Debug Info ---[/bold {BRAND_COLOR}]")
        console.print(f"[bold]URL:[/bold] {base_url.rstrip('/')}/chat/completions")
        console.print(f"[bold]Model:[/bold] {model}")
        console.print(f"[bold]Payload:[/bold]\n{json.dumps(payload, indent=2)}")

    try:
        url = f"{base_url.rstrip('/')}/chat/completions"
        # Increased timeout to 60.0s to allow for local model cold-starts
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            if verbose:
                console.print(f"\n[bold]Response Status:[/bold] {response.status_code}")
                console.print(f"[bold]Response Body:[/bold]\n{response.text}")
                
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
