# Import and expose configuration classes from the main config module
import sys
import os
from importlib.util import spec_from_file_location, module_from_spec

# Get the path to the root config.py file
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_file_path = os.path.join(backend_dir, 'config.py')

# Load the config module from the specific file
spec = spec_from_file_location("root_config", config_file_path)
root_config = module_from_spec(spec)
spec.loader.exec_module(root_config)

# Re-export the functions and classes
get_config = root_config.get_config
Config = root_config.Config
DevelopmentConfig = root_config.DevelopmentConfig
TestingConfig = root_config.TestingConfig
ProductionConfig = root_config.ProductionConfig

__all__ = ['get_config', 'Config', 'DevelopmentConfig', 'TestingConfig', 'ProductionConfig']