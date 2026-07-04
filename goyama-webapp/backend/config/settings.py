import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Absolute paths guaranteed to be inside the workspace
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
    
    @property
    def UI_ROOT(self) -> Path:
        return self.PROJECT_ROOT / "goyama-webapp"
        
    @property
    def TEMP_DIR(self) -> Path:
        if getattr(sys, 'frozen', False):
            path = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "GoyamaRecon" / "temp_sessions"
        else:
            path = self.UI_ROOT / "temp_sessions"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def RUN_HISTORY_DIR(self) -> Path:
        if getattr(sys, 'frozen', False):
            path = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "GoyamaRecon" / "run_history"
        else:
            path = self.UI_ROOT / "run_history"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def DEMO_DATA_DIR(self) -> Path:
        if getattr(sys, 'frozen', False):
            path = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "GoyamaRecon" / "demo_data"
        else:
            path = self.UI_ROOT / "demo_data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def DEFAULT_CONFIG_PATH(self) -> Path:
        # Check if the user specified a custom config path in production
        if getattr(sys, 'frozen', False):
            # In frozen app, check local appdata config first, then fall back to embedded config inside internal folder
            local_path = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "GoyamaRecon" / "recon_config.yaml"
            if local_path.exists():
                return local_path
            # Fallback to packaged one inside the PyInstaller internal extraction folder
            if hasattr(sys, '_MEIPASS'):
                embedded_path = Path(sys._MEIPASS) / "_internal" / "recon_config.yaml"
                if embedded_path.exists():
                    return embedded_path
                embedded_root_path = Path(sys._MEIPASS) / "recon_config.yaml"
                if embedded_root_path.exists():
                    return embedded_root_path
        return self.PROJECT_ROOT / "recon_config.yaml"

    class Config:
        env_prefix = "MFRECON_"

settings = Settings()
