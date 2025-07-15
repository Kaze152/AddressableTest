"""
Configuration Management

Handles configuration loading and management for the mobile automation framework.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for mobile automation"""
    
    _instance = None
    _config_data = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config_data:
            self.load_default_config()
    
    def load_default_config(self):
        """Load default configuration"""
        self._config_data = {
            'device': {
                'android': {
                    'default_timeout': 30,
                    'screenshot_format': 'png',
                    'click_delay': 0.1
                },
                'ios': {
                    'default_timeout': 30,
                    'screenshot_format': 'png',
                    'click_delay': 0.1
                }
            },
            'recognition': {
                'template_matching': {
                    'threshold': 0.8,
                    'method': 'TM_CCOEFF_NORMED'
                },
                'ocr': {
                    'language': 'ch',  # Chinese and English
                    'use_gpu': False,
                    'confidence_threshold': 0.7
                },
                'color_detection': {
                    'tolerance': 30
                }
            },
            'automation': {
                'retry_attempts': 3,
                'retry_delay': 1.0,
                'screenshot_before_action': True,
                'screenshot_after_action': False
            },
            'logging': {
                'level': 'INFO',
                'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}',
                'file_rotation': '10 MB',
                'file_retention': '7 days'
            }
        }
    
    def load_from_file(self, config_path: str):
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to configuration file
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                self._merge_config(file_config)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Recursively merge new configuration with existing"""
        def merge_dict(base: Dict, update: Dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
        
        merge_dict(self._config_data, new_config)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key path
        
        Args:
            key_path: Dot-separated key path (e.g., 'device.android.timeout')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._config_data
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value by dot-separated key path
        
        Args:
            key_path: Dot-separated key path
            value: Value to set
        """
        keys = key_path.split('.')
        config = self._config_data
        
        # Navigate to parent dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the final value
        config[keys[-1]] = value
    
    def save_to_file(self, config_path: str):
        """
        Save current configuration to YAML file
        
        Args:
            config_path: Path to save configuration file
        """
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration: {e}")
    
    def get_device_config(self, device_type: str) -> Dict[str, Any]:
        """
        Get device-specific configuration
        
        Args:
            device_type: 'android' or 'ios'
            
        Returns:
            Device configuration dictionary
        """
        return self.get(f'device.{device_type}', {})
    
    def get_recognition_config(self, method: str) -> Dict[str, Any]:
        """
        Get recognition method configuration
        
        Args:
            method: Recognition method ('template_matching', 'ocr', 'color_detection')
            
        Returns:
            Recognition configuration dictionary
        """
        return self.get(f'recognition.{method}', {})
    
    def get_automation_config(self) -> Dict[str, Any]:
        """
        Get automation configuration
        
        Returns:
            Automation configuration dictionary
        """
        return self.get('automation', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration
        
        Returns:
            Logging configuration dictionary
        """
        return self.get('logging', {})
    
    @classmethod
    def create_sample_config(cls, output_path: str):
        """
        Create a sample configuration file
        
        Args:
            output_path: Path to save sample configuration
        """
        config = cls()
        sample_config = {
            'device': {
                'android': {
                    'default_timeout': 30,
                    'adb_host': None,  # Use USB if None, or IP address for TCP
                    'adb_port': 5555,
                    'screenshot_format': 'png',
                    'click_delay': 0.1
                },
                'ios': {
                    'default_timeout': 30,
                    'device_udid': None,  # Use first available if None
                    'screenshot_format': 'png',
                    'click_delay': 0.1
                }
            },
            'recognition': {
                'template_matching': {
                    'threshold': 0.8,
                    'method': 'TM_CCOEFF_NORMED',
                    'multi_scale': True,
                    'scale_range': [0.8, 1.2],
                    'scale_step': 0.1
                },
                'ocr': {
                    'language': 'ch',  # 'ch' for Chinese+English, 'en' for English only
                    'use_gpu': False,
                    'confidence_threshold': 0.7,
                    'enable_mkldnn': True
                },
                'color_detection': {
                    'tolerance': 30,
                    'blur_kernel_size': 5
                }
            },
            'automation': {
                'retry_attempts': 3,
                'retry_delay': 1.0,
                'screenshot_before_action': True,
                'screenshot_after_action': False,
                'action_delay': 0.5
            },
            'logging': {
                'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
                'console_output': True,
                'file_output': True,
                'log_directory': 'logs',
                'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}',
                'file_rotation': '10 MB',
                'file_retention': '7 days'
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f, default_flow_style=False, allow_unicode=True)