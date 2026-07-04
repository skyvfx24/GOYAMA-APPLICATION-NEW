# Reconciliation Engine — Testing & Verification Guide

This guide explains how to configure, run, and debug the reconciliation engine's test suite both from the command line and directly within Visual Studio Code (VS Code).

---

## 1. CLI Testing Instructions

Before running the tests, ensure your virtual environment is activated and dependencies are installed.

### Step 1: Activate Virtual Environment
Open your terminal at the project root (`d:\pythonenginecrm`):

* **PowerShell**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **Command Prompt (CMD)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```

### Step 2: Run Pytest Commands

* **Run the entire test suite** (183 tests):
  ```powershell
  python -m pytest
  ```
* **Run only the new functional improvements tests**:
  ```powershell
  python -m pytest tests/test_functional_improvements.py
  ```
* **Run with verbose output** (shows individual test names):
  ```powershell
  python -m pytest -v
  ```
* **Run a specific test case** within a file:
  ```powershell
  python -m pytest tests/test_functional_improvements.py::test_incomplete_crm_suppressed
  ```

---

## 2. VS Code Testing Setup (UI Integration)

VS Code provides a graphical **Testing Panel** to execute and debug tests line-by-line. Follow these steps to configure it:

### Step 1: Install Required VS Code Extensions
Ensure you have the official extensions installed:
1. Open the Extensions View in VS Code (`Ctrl + Shift + X`).
2. Search for and install:
   - **Python** (by Microsoft)

### Step 2: Select the Python Interpreter
Ensure VS Code is using the Python executable from your virtual environment:
1. Open the Command Palette (`Ctrl + Shift + P`).
2. Type and select: `Python: Select Interpreter`.
3. Choose the option pointing to your virtual environment: `.\venv\Scripts\python.exe`.

### Step 3: Configure Pytest in VS Code
1. Open the Command Palette (`Ctrl + Shift + P`).
2. Type and select: `Python: Configure Tests`.
3. Select **pytest** as the test framework.
4. Select **Root directory** (`.`) as the test discovery location.

*Alternatively, VS Code will auto-generate/read this `.vscode/settings.json` file:*
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

### Step 4: Run Tests via the Testing Panel
1. Click the **Testing** icon (shaped like a chemistry beaker) on the left Sidebar.
2. Click the **Refresh** icon to discover tests.
3. You will see a folder hierarchy of all test files.
4. Hover over `test_functional_improvements.py` or any test case and click the **Play** button to run.

---

## 3. Debugging Tests in VS Code

Debugging allows you to pause execution, inspect variables, and step through the reconciliation rules:

1. Open a test file (e.g., [test_functional_improvements.py](file:///d:/pythonenginecrm/tests/test_functional_improvements.py)).
2. Set a **breakpoint** by clicking to the left of any line number in your test or source code (a red dot will appear).
3. Navigate to the **Testing Panel** sidebar.
4. Right-click the test case you want to inspect and select **Debug Test** (or click the bug icon next to the test case).
5. VS Code will launch the debugger and pause execution at your breakpoint.
