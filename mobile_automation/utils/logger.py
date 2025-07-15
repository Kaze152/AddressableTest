"""
Logging System

Provides centralized logging functionality for the mobile automation framework.
"""

import sys
from pathlib import Path
from typing import Optional
from loguru import logger


class Logger:
    """Centralized logger for mobile automation framework"""
    
    _initialized = False
    _loggers = {}
    
    @classmethod
    def initialize(cls, config: Optional[dict] = None):
        """
        Initialize the logging system
        
        Args:
            config: Logging configuration dictionary
        """
        if cls._initialized:
            return
        
        # Default configuration
        default_config = {
            'level': 'INFO',
            'console_output': True,
            'file_output': True,
            'log_directory': 'logs',
            'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}',
            'file_rotation': '10 MB',
            'file_retention': '7 days'
        }
        
        if config:
            default_config.update(config)
        
        # Remove default handler
        logger.remove()
        
        # Console output
        if default_config['console_output']:
            logger.add(
                sys.stderr,
                level=default_config['level'],
                format=default_config['format']
            )
        
        # File output
        if default_config['file_output']:
            log_dir = Path(default_config['log_directory'])
            log_dir.mkdir(exist_ok=True)
            
            logger.add(
                log_dir / "mobile_automation_{time:YYYY-MM-DD}.log",
                level=default_config['level'],
                format=default_config['format'],
                rotation=default_config['file_rotation'],
                retention=default_config['file_retention'],
                encoding='utf-8'
            )
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str):
        """
        Get a named logger instance
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        if not cls._initialized:
            cls.initialize()
        
        if name not in cls._loggers:
            cls._loggers[name] = logger.bind(name=name)
        
        return cls._loggers[name]
    
    @classmethod
    def set_level(cls, level: str):
        """
        Set logging level for all loggers
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        logger.level(level.upper())
    
    @classmethod
    def debug(cls, message: str, name: str = "Global"):
        """Log debug message"""
        cls.get_logger(name).debug(message)
    
    @classmethod
    def info(cls, message: str, name: str = "Global"):
        """Log info message"""
        cls.get_logger(name).info(message)
    
    @classmethod
    def warning(cls, message: str, name: str = "Global"):
        """Log warning message"""
        cls.get_logger(name).warning(message)
    
    @classmethod
    def error(cls, message: str, name: str = "Global"):
        """Log error message"""
        cls.get_logger(name).error(message)
    
    @classmethod
    def critical(cls, message: str, name: str = "Global"):
        """Log critical message"""
        cls.get_logger(name).critical(message)


# Initialize with default settings
Logger.initialize()