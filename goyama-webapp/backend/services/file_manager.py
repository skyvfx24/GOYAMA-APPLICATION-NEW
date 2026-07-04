import os
import shutil
import time
from pathlib import Path
from typing import Optional
from loguru import logger
from backend.config.settings import settings

class FileManager:
    """Handles session-scoped file writes, path lookups, and auto-cleanup tasks."""

    @staticmethod
    def save_file(file_id: str, filename: str, content: bytes) -> Path:
        """Saves file content to a unique folder named by file_id, preserving filename."""
        folder = settings.TEMP_DIR / file_id
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        logger.info(f"File saved successfully: {file_path}")
        return file_path

    @staticmethod
    def get_file_path(file_id: str) -> Optional[Path]:
        """Finds the file path inside the file_id folder, returning None if not found."""
        folder = settings.TEMP_DIR / file_id
        if not folder.exists() or not folder.is_dir():
            return None
            
        # The file is the only file or first file inside this directory
        children = list(folder.iterdir())
        if not children:
            return None
            
        return children[0]

    @staticmethod
    def cleanup_old_files(max_age_seconds: int = 3600) -> None:
        """Deletes session directories that are older than the specified max age."""
        now = time.time()
        logger.info("Executing file manager cleanup task...")
        
        # Clean Temp sessions
        if settings.TEMP_DIR.exists():
            for child in settings.TEMP_DIR.iterdir():
                if child.is_dir():
                    try:
                        mtime = child.stat().st_mtime
                        if now - mtime > max_age_seconds:
                            logger.info(f"Cleaning up old temp session: {child}")
                            shutil.rmtree(child)
                    except Exception as e:
                        logger.error(f"Failed to delete {child}: {e}")

file_manager = FileManager()
