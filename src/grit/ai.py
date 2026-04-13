import os
import json
import re
from typing import List, Optional

from loguru import logger
from pydantic import BaseModel, ValidationError
from pydantic_ai import Agent


# =========================
# Schema
# =========================
class CommitMessage(BaseModel):
    type: str
    scope: str
    message: str
    body: List[str]


# =========================
# Repair Layer
# =========================
def _indestructible_surgical_repair(text: str) -> str:
    text = "".join(c for c in text if ord(c) >= 32 or c in "\n\r\t")

    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if not match:
        return text

    raw = match.group(1).strip()

    raw = re.sub(r',(\s*[}\]])', r'\1', raw)
    raw = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', raw)
    raw = raw.replace("'", '"')

    try:
        data = json.loads(raw)

        if isinstance(data, dict) and "type" not in data:
            for v in data.values():
                if isinstance(v, dict) and "type" in v:
                    data = v
                    break

        if not isinstance(data, dict):
            raise ValueError("Not dict")

        if not all(k in data for k in ["type", "scope", "message", "body"]):
            raise ValueError("Missing keys")

        if not isinstance(data["body"], list):
            data["body"] = [str(data["body"])]

        return json.dumps(data)

    except Exception:
        obj = {}

        for key in ["type", "scope", "message"]:
            m = re.search(rf'"{key}"\s*:\s*"([^"]+)"', raw)
            if m:
                obj[key] = m.group(1)

        m_body = re.search(r'"body"\s*:\s*\[(.*?)\]', raw, re.DOTALL)
        if m_body:
            items = re.findall(r'"([^"]+)"', m_body.group(1))
            if items:
                obj["body"] = items

        if all(k in obj for k in ["type", "scope", "message"]):
            obj.setdefault("body", ["Recovered insight."])
            return json.dumps(obj)

    return raw


# =========================
# Main Generator
# =========================
def generate_commit_message(
    diff: str,
    base_url: str,
    api_key: str,
    model_name: str,
    verbose: bool = False,
) -> Optional[str]:

    if not diff.strip():
        logger.error("Empty diff.")
        return None

    clean_url = None if base_url in ["Not configured", ""] else base_url
    clean_key = None if api_key in ["Not configured", ""] else api_key

    provider_prefix = "ollama" if clean_url and "11434" in clean_url else "openai"
    full_model_string = f"{provider_prefix}:{model_name}"

    # =========================
    # ENV (RESTORED + OPTIMIZED)
    # =========================
    env_vars = {}

    if provider_prefix == "ollama":
        env_vars.update({
            "OLLAMA_API_KEY": clean_key or "ollama",
            "OLLAMA_NUM_CTX": "2048",
            "OLLAMA_NUM_PREDICT": "128",
            "OLLAMA_NUM_GPU": "1",
            "OLLAMA_NUM_THREAD": "4",
            "OLLAMA_KEEP_ALIVE": "5m",
            "OLLAMA_MAX_LOADED_MODELS": "1",
        })

        if clean_url:
            env_vars["OLLAMA_BASE_URL"] = clean_url

    original_env = {k: os.environ.get(k) for k in env_vars}
    os.environ.update(env_vars)

    try:
        from grit.executor import get_staged_files

        staged_files = get_staged_files()
        files_list = "\n".join(f"- {f}" for f in staged_files)

        instructions = """
You are NOT a chatbot.
You are a strict JSON generator.
Output ONLY valid JSON.
"""

        agent = Agent(
            full_model_string,
            instructions=instructions,
        )

        last_error = None

        try:
            summary_prompt = f"Summarize this git diff in 1 concise sentence:\n{diff}"
            diff_summary = agent.run_sync(summary_prompt).output.strip()
        except Exception:
            diff_summary = diff[:500]

        for attempt in range(4):
            try:
                prompt = f"""
FILES:
{files_list}

SUMMARY:
{diff_summary}

Respond with EXACTLY this JSON structure:

{{
  "type": "...",
  "scope": "...",
  "message": "...",
  "body": ["...", "..."]
}}

Rules:
- No extra keys
- No comments
- No trailing text
- body MUST be array of strings
- Output ONLY JSON

Now produce the JSON:
"""

                if last_error:
                    prompt += f"\nFix previous error:\n{last_error}\n"

                # =========================
                # PREFILL JSON (Point 3)
                # =========================
                prompt += '\n{\n  "type": "'

                result = agent.run_sync(prompt)
                raw_output = result.output.strip()

                if verbose:
                    logger.debug(f"RAW:\n{raw_output}")

                if not raw_output.startswith("{"):
                    raise ValueError("Did not start with JSON")

                if '"code"' in raw_output.lower():
                    raise ValueError("Model returned code")

                clean_json = _indestructible_surgical_repair(raw_output)

                msg_obj = CommitMessage.model_validate_json(clean_json)

                header = f"{msg_obj.type}({msg_obj.scope}): {msg_obj.message}"
                body = "\n".join(f"- {b}" for b in msg_obj.body)

                return f"{header}\n\n{body}"

            except (ValidationError, Exception) as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt+1} failed: {e}")

        return None

    finally:
        for k, v in original_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v