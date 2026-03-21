"""
Centralized constants for the Grit CLI.
"""
from pathlib import Path

# =========================
# File System & Paths
# =========================

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

# =========================
# Billion Dollar Design System
# =========================
# These constants define the sacred visual identity of Grit.
BRAND_COLOR = "bright_cyan"  # Primary teal/blue brand highlight
SUCCESS_COLOR = "spring_green3"  # For checkmarks and completion
WARN_COLOR = "gold1"  # For warnings and non-blocking issues
ERROR_COLOR = "deep_pink3"  # For fatal errors or destructive prompts
ACCENT_COLOR = "bright_cyan"  # Secondary highlights (standardized to brand color)

# =========================
# AI & CommitScribe
# =========================
COMMIT_TYPES = ["feat", "fix", "docs", "style", "refactor", "test", "chore"]

# Limits for AI processing
DIFF_TRUNCATION_LIMIT = 8000
RAW_DIFF_PROMPT_LIMIT = 4000
AI_RETRIES = 2
MAX_DRAFT_HISTORY = 50

# Quote rotation for AI analysis
QUOTE_CHANGE_INTERVAL_SECONDS = 4.0
AI_ANALYSIS_QUOTES = [
    "Grit: Making your laziness look like genius...",
    "CommitScribe is judging your variable names...",
    "Fixing your history because you couldn't...",
    "Adding 'architectural rationale' to your 'idk'...",
    "Your streak is safe with me. Shhh...",
    "Polishing this turd of a diff...",
    "Translating 'it works' to 'high-fidelity solution'...",
    "Git doesn't have to know you took a nap...",
    "Turning your chaos into conventional commits...",
    "CommitScribe: Smarter than your last 10 messages...",
    "Making your commit graph look busy for once...",
    "Sassing your code into a professional draft...",
    "Real developers use Grit. Lazy ones do too...",
    "Stop 'oops'-ing and start Gritting...",
    "Your history called. It's embarrassed. Fixing...",
    "Drafting wisdom from your 3 AM brain-dump...",
    "Streaks are earned. Or just Grit-ted...",
    "CommitScribe: Your PR's secret weapon...",
    "Making your commits look like they belong in a museum...",
    "Less 'fix', more Grit..."
]

# Ollama defaults
OLLAMA_NUM_CTX = "4096"
OLLAMA_NUM_PREDICT = "256"
OLLAMA_NUM_GPU = "1"
OLLAMA_KEEP_ALIVE = "10m"
OLLAMA_MAX_LOADED_MODELS = "1"

# =========================
# TUI & UX Settings
# =========================
KEY_READ_TIMEOUT = 0.1
ESCAPE_SEQ_TIMEOUT = 0.02
UI_REFRESH_RATE = 10
STAGE_PICKER_OVERHEAD_LINES = 14
VICTORY_ANIMATION_DURATION = 12
VICTORY_ANIMATION_SLEEP = 0.08

# =========================
# Sync & External APIs
# =========================
YEAR_DAYS = 365
HOUR_SECONDS = 3600
GITHUB_CONTRIBUTIONS_TIMEOUT = 10.0
UPDATE_CHECK_TIMEOUT = 1.5
