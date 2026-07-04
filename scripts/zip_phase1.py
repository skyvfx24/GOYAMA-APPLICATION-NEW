import shutil
import zipfile
from pathlib import Path

def create_zip():
    base_dir = Path(__file__).resolve().parents[1]
    archive_name = base_dir / "mfrecon_phase2"
    
    # We want to zip mfrecon/, tests/, pyproject.toml, requirements.txt, recon_config.yaml, README.md
    items_to_zip = [
        "mfrecon",
        "tests",
        "pyproject.toml",
        "requirements.txt",
        "recon_config.yaml",
        "README.md",
        "docs/system_architecture.md"
    ]
    
    zip_path = base_dir / "mfrecon_phase2.zip"
    print(f"Creating ZIP archive at: {zip_path}")
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item_name in items_to_zip:
            item_path = base_dir / item_name
            if not item_path.exists():
                print(f"Warning: {item_name} does not exist, skipping.")
                continue
            
            if item_path.is_file():
                zip_file.write(item_path, arcname=item_name)
                print(f"Added file: {item_name}")
            elif item_path.is_dir():
                for file_path in item_path.rglob("*"):
                    if file_path.is_file() and "__pycache__" not in file_path.parts and ".pytest_cache" not in file_path.parts:
                        # compute relative path for zip archive
                        rel_path = file_path.relative_to(base_dir)
                        zip_file.write(file_path, arcname=str(rel_path))
                print(f"Added directory: {item_name}")
                
    print("ZIP creation completed successfully.")

if __name__ == "__main__":
    create_zip()
