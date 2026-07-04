import zipfile
from pathlib import Path

def create_zip():
    base_dir = Path(__file__).resolve().parents[1]
    releases_dir = base_dir / "releases"
    releases_dir.mkdir(exist_ok=True)
    zip_path = releases_dir / "mfrecon_phase8.zip"
    print(f"Creating ZIP archive at: {zip_path}")
    
    items_to_zip = [
        "mfrecon",
        "tests",
        "docs",
        "examples",
        "dist",
        "pyproject.toml",
        "requirements.txt",
        "recon_config.yaml",
        "README.md",
        "scripts",
        "sample_run",
        "goyama-webapp"
    ]
    
    exclude_dirs = {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "mfrecon.egg-info",
        "build",
        "node_modules"
    }
    
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
                    if file_path.is_file():
                        # Check if any parent component is in exclude_dirs
                        parts_set = set(file_path.parts)
                        if parts_set.intersection(exclude_dirs):
                            continue
                        # compute relative path for zip archive
                        rel_path = file_path.relative_to(base_dir)
                        zip_file.write(file_path, arcname=str(rel_path))
                print(f"Added directory: {item_name}")
                
    print(f"ZIP creation completed successfully. Archive size: {zip_path.stat().st_size} bytes")

if __name__ == "__main__":
    create_zip()
