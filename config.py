import os
from enum import Enum
from typing import Optional

class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class Config:
    """Environment-based configuration."""
    
    def __init__(self):
        self.env = self._get_environment()
        
    def _get_environment(self) -> Environment:
        """Determine current environment from ENV variable or default to production."""
        env_str = os.getenv("ENV", "production").lower()
        try:
            return Environment(env_str)
        except ValueError:
            # Default to production for safety if invalid env provided
            return Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == Environment.PRODUCTION
    
    @property
    def enable_stream_logging(self) -> bool:
        """Enable detailed stream logging only in development."""
        return self.is_development
    
    @property
    def verbose_logging(self) -> bool:
        """Enable verbose Claude command logging in development."""
        return self.is_development
    
    @property
    def log_level(self) -> str:
        """Get appropriate log level."""
        return "DEBUG" if self.is_development else "INFO"

# Global config instance
config = Config()