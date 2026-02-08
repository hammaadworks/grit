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
DEFAULT_COMMIT_TYPES_STR = ",".join(COMMIT_TYPES)

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
    "Less 'fix', more Grit...",
    "Fetching the best commit message...",
    "Cooking a 5-star commit message...",
    "Main character energy for your PR...",
    "Staging area vibes: Immaculate...",
    "Giving your diff a major glow-up...",
    "No cap, this message is fire...",
    "Built different. Grit different...",
    "Big Brain diff analysis incoming...",
    "Slapping some logic on this branch...",
    "Your contribution graph is eating...",
    "Immense W in this staged diff...",
    "Architectural vibes only, no cap...",
    "Peak Git performance detected...",
    "Translating 'it works' to 'legendary'...",
    "Sassing your diff into a masterpiece...",
    "Real devs use Grit. Facts...",
    "Stop 'oops'-ing. Start Cooking...",
    "Your graph called. It's thriving...",
    "Refining that 3 AM branch-dump...",
    "Streaks are earned. Or Grit-ted...",
    "Your PR's secret sauce is loading...",
    "Commits so good they're viral...",
    "Less 'fix', more 'visionary' logic...",
    "Staging files with main character energy...",
    "Giving WIP a major promotion...",
    "Better English than your commit history...",
    "Git is hard. Grit is a whole mood...",
    "Spaghetti? No, 'artisan staged pasta'...",
    "Your streak's main character moment...",
    "Win the repo. Win with Grit...",
    "I've seen your diffs. Pure heat...",
    "Forgot a file? Let's call it 'synergy'...",
    "Surgical strikes on your git log...",
    "Passing PRs with immaculate energy...",
    "Turning 'idk' into 'technical wisdom'...",
    "Teaching Git some real style...",
    "Commit like a pro. Grit like a boss...",
    "This diff is absolutely valid. Period.",
    "This diff is absolutely wild. Period.",
    "LGTM! Let's Gamble, Try Merging...",
    "LGTM! Looks Gorgeous, To Me...",
    "LGTM! Leave Grit To Marinate..."
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
