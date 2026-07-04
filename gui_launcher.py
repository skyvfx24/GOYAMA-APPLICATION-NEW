import os
import sys
import time
import threading
import multiprocessing
import webbrowser
import uvicorn

from pathlib import Path

try:
    import webview
except ImportError:
    webview = None

# Add project root and goyama-webapp to sys.path so backend and mfrecon can be found
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
WEBAPP_ROOT = PROJECT_ROOT / "goyama-webapp"
if str(WEBAPP_ROOT) not in sys.path:
    sys.path.insert(0, str(WEBAPP_ROOT))


def start_backend():
    try:
        from backend.main import app
    except Exception as e:
        print(f"FastAPI backend import error: {e}")
        raise

    # Deactivate uvicorn signal handlers as uvicorn is running in a daemon thread
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning", loop="asyncio")
    server = uvicorn.Server(config)
    server.run()


def get_asset_path():
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "dist")
    return os.path.join(str(PROJECT_ROOT), "dist")


def open_default_browser(url: str) -> None:
    print(f"Opening default browser at {url}")
    webbrowser.open(url, new=2, autoraise=True)


def keep_backend_alive(thread: threading.Thread) -> None:
    try:
        while thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Shutting down backend...")


if __name__ == '__main__':
    # Required for frozen executables utilizing multiprocessing (e.g. pandas/rapidfuzz)
    multiprocessing.freeze_support()
    
    # Configure production static asset directory environment variable
    os.environ["MFRECON_ASSET_DIR"] = get_asset_path()

    # Start FastAPI backend in a background daemon thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # Wait for uvicorn server to bind to local port
    time.sleep(1.5)

    url = "http://127.0.0.1:8000/"
    if webview is not None:
        webview.create_window(
            title="Goyama Financial Reconciliation System",
            url=url,
            width=1366,
            height=850,
            resizable=True,
            min_size=(1024, 768)
        )
        webview.start()
    else:
        print("pywebview is not installed. Falling back to the default browser.")
        open_default_browser(url)
        keep_backend_alive(backend_thread)
