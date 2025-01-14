import sys
from pathlib import Path
from loguru import logger

def setup_logger(verbose: bool = False):
    """
    Configures Loguru for professional project-wide logging.
    - Console: Shows SUCCESS/INFO by default, DEBUG if verbose.
    - File: Always records DEBUG in ~/.grit/logs/grit.log
    """
    # Remove default handler
    logger.remove()

    # Determine log path
    log_dir = Path.home() / ".grit" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "grit.log"

    # 1. Console Handler (High-signal for user)
    level = "DEBUG" if verbose else "INFO"
    
    # Custom format for a clean CLI feel
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        level=level,
        format=fmt,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # 2. File Handler (Persistent for debugging)
    logger.add(
        str(log_file),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )

    if verbose:
        logger.debug(f"Logger initialized at level: {level}")
        logger.debug(f"Log file: {log_file}")

    return logger
