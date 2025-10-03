# logs/config.py
"""
Centralized logging configuration for all components.
Provides standardized logging paths and configuration.
"""

from pathlib import Path
import os

# Base logs directory
LOGS_DIR = Path(__file__).parent
LOGS_DIR.mkdir(exist_ok=True)

# Create subdirectories for organized logging
(LOGS_DIR / "api").mkdir(exist_ok=True)
(LOGS_DIR / "agents").mkdir(exist_ok=True)
(LOGS_DIR / "app").mkdir(exist_ok=True)
(LOGS_DIR / "database").mkdir(exist_ok=True)
(LOGS_DIR / "system").mkdir(exist_ok=True)
(LOGS_DIR / "docs_loader").mkdir(exist_ok=True)

class LogConfig:
    """Centralized logging configuration for all components."""
    
    # API logs
    API_LOG = LOGS_DIR / "api" / "api.log"
    API_ACCESS_LOG = LOGS_DIR / "api" / "access.log"
    API_ERROR_LOG = LOGS_DIR / "api" / "error.log"
    
    # Agent logs
    CHATBOT_LOG = LOGS_DIR / "agents" / "chatbot.log"
    TOKEN_LOG = LOGS_DIR / "agents" / "token_tracking.log"
    LLM_TOOLS_LOG = LOGS_DIR / "agents" / "llm_tools.log"
    
    # App logs (Streamlit)
    STREAMLIT_LOG = LOGS_DIR / "app" / "streamlit.log"
    USER_ACTIVITY_LOG = LOGS_DIR / "app" / "user_activity.log"
    UI_LOG = LOGS_DIR / "app" / "ui.log"
    
    # Database logs
    DATABASE_LOG = LOGS_DIR / "database" / "db_operations.log"
    MIGRATION_LOG = LOGS_DIR / "database" / "migrations.log"
    
    # System logs
    APPLICATION_LOG = LOGS_DIR / "system" / "application.log"
    ERROR_LOG = LOGS_DIR / "system" / "errors.log"
    PERFORMANCE_LOG = LOGS_DIR / "system" / "performance.log"
    EVALUATION_LOG = LOGS_DIR / "system" / "evaluation.log"
    
    # Docs loader logs
    DOCS_LOADER_LOG = LOGS_DIR / "docs_loader" / "docs_loader.log"
    CHROMA_DEBUG_LOG = LOGS_DIR / "docs_loader" / "chroma_debug.log"
    VECTOR_DEBUG_LOG = LOGS_DIR / "docs_loader" / "vector_debug.log"
    CLEANUP_LOG = LOGS_DIR / "docs_loader" / "cleanup.log"
    SIMILARITY_LOG = LOGS_DIR / "docs_loader" / "similarity.log"
    
    # Standard log format
    STANDARD_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"
    API_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | API | {message}"
    AGENT_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | AGENT | {message}"
    APP_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | APP | {message}"
    
    @classmethod
    def get_api_log(cls):
        """Get API log path."""
        return str(cls.API_LOG)
    
    @classmethod
    def get_api_error_log(cls):
        """Get API error log path."""
        return str(cls.API_ERROR_LOG)
    
    @classmethod
    def get_chatbot_log(cls):
        """Get chatbot log path."""
        return str(cls.CHATBOT_LOG)
    
    @classmethod
    def get_token_log(cls):
        """Get token tracking log path."""
        return str(cls.TOKEN_LOG)
    
    @classmethod
    def get_streamlit_log(cls):
        """Get Streamlit app log path."""
        return str(cls.STREAMLIT_LOG)
    
    @classmethod
    def get_database_log(cls):
        """Get database operations log path."""
        return str(cls.DATABASE_LOG)
    
    @classmethod
    def get_docs_loader_log(cls):
        """Get docs loader log path."""
        return str(cls.DOCS_LOADER_LOG)
    
    @classmethod
    def get_chroma_debug_log(cls):
        """Get ChromaDB debug log path."""
        return str(cls.CHROMA_DEBUG_LOG)

    @classmethod
    def get_evaluation_debug_log(cls):
        """Get evaluation debug log path."""
        return str(cls.EVALUATION_LOG)
    
    @classmethod
    def get_vector_debug_log(cls):
        """Get vector debug log path."""
        return str(cls.VECTOR_DEBUG_LOG)
    
    @classmethod
    def get_cleanup_log(cls):
        """Get cleanup log path."""
        return str(cls.CLEANUP_LOG)
    
    @classmethod
    def get_error_log(cls):
        """Get system error log path."""
        return str(cls.ERROR_LOG)
    
    @classmethod
    def get_all_paths(cls):
        """Get all configured log paths for debugging."""
        return {
            "api_log": cls.get_api_log(),
            "api_error_log": cls.get_api_error_log(),
            "chatbot_log": cls.get_chatbot_log(),
            "token_log": cls.get_token_log(),
            "streamlit_log": cls.get_streamlit_log(),
            "database_log": cls.get_database_log(),
            "docs_loader_log": cls.get_docs_loader_log(),
            "chroma_debug_log": cls.get_chroma_debug_log(),
            "vector_debug_log": cls.get_vector_debug_log(),
            "cleanup_log": cls.get_cleanup_log(),
            "error_log": cls.get_error_log()
        }

# Common logging configuration function
def setup_logger(logger, log_path, format_string=None, level="INFO", rotation="1 week", retention="4 weeks"):
    """
    Setup a logger with standard configuration.
    
    Args:
        logger: The loguru logger instance
        log_path: Path to the log file
        format_string: Log format (uses STANDARD_FORMAT if None)
        level: Log level (default: INFO)
        rotation: Log rotation setting (default: 1 week)
        retention: Log retention setting (default: 4 weeks)
    """
    if format_string is None:
        format_string = LogConfig.STANDARD_FORMAT
    
    logger.add(
        log_path,
        format=format_string,
        level=level,
        rotation=rotation,
        retention=retention
    )
    
    # Also add error logging to system error log
    if log_path != str(LogConfig.ERROR_LOG):
        logger.add(
            LogConfig.ERROR_LOG,
            format=format_string,
            level="ERROR",
            rotation=rotation,
            retention=retention
        )

# Initialize directory structure
def initialize_log_directories():
    """Ensure all log directories exist."""
    for attr_name in dir(LogConfig):
        if attr_name.endswith('_LOG') and not attr_name.startswith('_'):
            log_path = getattr(LogConfig, attr_name)
            log_path.parent.mkdir(parents=True, exist_ok=True)

# Initialize on import
initialize_log_directories()
