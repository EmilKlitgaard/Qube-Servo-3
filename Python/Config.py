import os
import yaml

class Config:
    _instance = None

    # Singleton pattern: only one instance of Config will exist, and it will be shared across all imports.
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    # Load configuration from Config.yaml and set attributes
    def _load(self):
        yaml_path = os.path.join(os.path.dirname(__file__), 'Config.yaml')
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)

        # Flat keys (e.g. DEBUG) become attributes directly.
        # Nested sections (e.g. UART.PORT) become SECTION_KEY (e.g. UART_PORT).
        for section, params in data.items():
            if isinstance(params, dict):
                for var, value in params.items():
                    setattr(self, f"{section}_{var}", value)
            else:
                setattr(self, section, params)

        if self.DEBUG:
            for key, value in vars(self).items():
                print(f"[Config] {key} = {value}")
            print()

# Global — import this anywhere: `from Config import config`
config = Config()
