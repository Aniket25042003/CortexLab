"""
Logging Configuration

Centralized logging setup for the CortexLab backend.
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.FileHandler(log_dir / "cortexlab.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # File handler for agent-specific logs
    agent_handler = logging.FileHandler(log_dir / "agents.log")
    agent_handler.setLevel(logging.DEBUG)
    agent_handler.setFormatter(detailed_formatter)
    
    # Add agent handler to agent loggers
    agent_logger = logging.getLogger("app.agents")
    agent_logger.addHandler(agent_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    
    logging.info("Logging initialized")


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get a logger for a specific agent node."""
    return logging.getLogger(f"app.agents.nodes.{agent_name}")
