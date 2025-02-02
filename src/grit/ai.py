import os
from typing import List, Optional, Literal

from loguru import logger
from pydantic import BaseModel, ValidationError, Field
from pydantic_ai import Agent


# =========================
# Schema
# =========================
class CommitMessage(BaseModel):
    """
    Structured commit message following Conventional Commits.
    """
    type: Literal["feat", "fix", "docs", "style", "refactor", "test", "chore"] = Field(
        description="The type of the change: feat (new feature), fix (bug fix), docs (documentation), style (formatting), refactor (code change), test (adding tests), chore (maintenance)"
    )
    scope: str = Field(description="The architectural scope affected (e.g. core, cli, ui, allocator)")
    message: str = Field(description="A concise summary of the change in the imperative mood")
    body: List[str] = Field(description="Detailed points explaining the rationale, impact, or future implications")


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

    # Detect provider based on URL or model name
    if clean_url and "11434" in clean_url:
        provider_prefix = "ollama"
    elif "gemini" in model_name.lower():
        provider_prefix = "google-gla"
    else:
        provider_prefix = "openai"

    full_model_string = f"{provider_prefix}:{model_name}"

    # =========================
    # ENV (RESTORED + OPTIMIZED)
    # =========================
    env_vars = {}

    if provider_prefix == "ollama":
        env_vars.update({
            "OLLAMA_API_KEY": clean_key or "ollama",
            "OLLAMA_NUM_CTX": "4096", # Increased context for larger diffs
            "OLLAMA_NUM_PREDICT": "256", # Enough for header + body
            "OLLAMA_NUM_GPU": "1", # Use Metal on Mac
            "OLLAMA_KEEP_ALIVE": "10m", # Keep in memory longer for back-to-back commits
            "OLLAMA_MAX_LOADED_MODELS": "1",
        })
        if clean_url:
            env_vars["OLLAMA_BASE_URL"] = clean_url
    elif provider_prefix == "google-gla":
        if clean_key:
            env_vars["GEMINI_API_KEY"] = clean_key
            env_vars["GOOGLE_API_KEY"] = clean_key
    elif provider_prefix == "openai":
        if clean_key:
            env_vars["OPENAI_API_KEY"] = clean_key
        if clean_url:
            env_vars["OPENAI_BASE_URL"] = clean_url

    original_env = {k: os.environ.get(k) for k in env_vars}
    os.environ.update(env_vars)

    try:
        from grit.executor import get_staged_files

        staged_files = get_staged_files()
        files_list = "\n".join(f"- {f}" for f in staged_files)

        instructions = (
            "You are a Distinguished System Architect creating high-fidelity Conventional Commit messages.\n"
            "Analyze the staged files and the diff to create a commit message that reflects technical wisdom.\n"
            "The message must be structured, professional, and explain the WHY behind the changes.\n"
            "Respond ONLY with the requested structured output."
        )

        agent = Agent(
            full_model_string,
            output_type=CommitMessage,
            instructions=instructions,
            retries=2, # Reduced retries to save time on slow models
        )

        prompt = f"""
STAGED FILES:
{files_list}

RAW DIFF:
{diff[:4000]}

Generate a Conventional Commit message. 
The 'type' MUST be one of: feat, fix, docs, style, refactor, test, chore.
The 'scope' should be the primary module or component affected.
The 'message' should be a high-level summary.
The 'body' MUST be a list of strings explaining rationale and impact.
"""

        try:
            result = agent.run_sync(prompt)
            msg_obj = result.output

            if verbose:
                logger.debug(f"AI GEN RESULT: {msg_obj}")

            header = f"{msg_obj.type}({msg_obj.scope}): {msg_obj.message}"
            body = "\n".join(f"- {b}" for b in msg_obj.body)

            return f"{header}\n\n{body}"

        except (ValidationError, Exception) as e:
            logger.warning(f"Generation failed: {e}")
            return None

    finally:
        for k, v in original_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
