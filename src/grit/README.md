# ⚙️ Grit Core Engine

This directory contains the heart of Grit—a high-performance Python engine that blends Git's robustness with modern AI intelligence. It is designed to be fast, type-safe, and highly interactive.

## 🏗 Architecture

The engine is built on three primary pillars:

1.  **Interactive TUI**: Powered by `Rich` and `Typer`, providing a fluid, high-fidelity terminal experience.
2.  **AI Intelligence**: Leveraging `Pydantic AI` for structured, context-aware commit analysis and message generation.
3.  **Deterministic Allocation**: A custom date-shifting algorithm that ensures streak consistency while maintaining Git integrity.

## 📂 Key Modules

- **`ai.py`**: The AI orchestration layer. It manages interactions with LLM providers (Gemini, OpenAI, Ollama) and defines the structured data models for commit analysis.
- **`allocator.py`**: The "brains" behind streak protection. It calculates optimal commit dates based on user targets and historical gaps.
- **`executor.py`**: A safe wrapper around Git commands. It ensures that all history manipulations are performed correctly and can be undone if necessary.
- **`state.py`**: Handles local persistence of configuration, AI drafts, and streak metadata.
- **`dashboard.py`**: The bridge between the CLI engine and the web-based intelligence dashboard.

## 🚀 Development Setup

To work on the core engine, ensure you have `uv` installed.

1.  **Clone and Install**:
    ```bash
    uv sync
    ```
2.  **Run in Development**:
    ```bash
    uv run grit --help
    ```

## 🧪 Testing

The engine maintains high reliability through an extensive test suite.

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/grit
```

---

> [!NOTE]
> Contributions to the core engine should prioritize type safety (using Pydantic models) and maintain the high-fidelity UI standards set by the project.
