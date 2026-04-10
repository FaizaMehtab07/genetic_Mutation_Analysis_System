"""
Logging configuration
"""

import logging
import logging.config
from ..core.config import settings
from pathlib import Path

def setup_logging():
    """Setup application logging"""

    # Create logs directory if needed
    settings.log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=settings.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console
            logging.FileHandler(settings.log_dir / 'app.log')  # File
        ]
    )

    # Avoid reload loops when uvicorn/watchfiles logs are written into files
    # inside the watched backend directory.
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").propagate = False

    return logging.getLogger(__name__)

logger = setup_logging()
