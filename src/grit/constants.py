"""
Centralized constants for the Grit CLI.
"""

# Files and extensions to exclude from AI diff analysis to save memory and tokens.
# These are typically high-volume, low-signal files like lockfiles or configs.
AI_FILE_EXCLUDE = [
    "*.lock",
    "uv.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "*.toml",
    "pyproject.toml",
    "*.json",
    "*.xml",
    "*.yaml",
    "*.yml",
]
