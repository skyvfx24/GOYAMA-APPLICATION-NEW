
# Mutual Fund Reconciliation System — Team Startup & Operations Guide

This guide describes how to set up, run, and verify the Mutual Fund Reconciliation Engine library and web dashboard on Windows.

---

## 1. Prerequisites & Version Requirements

Before proceeding, verify that you have the following environments installed:

* **Python**: Version **3.10** or higher (tested on **3.14.3**)
* **Node.js**: Version **18.0.0** or higher (tested on **v20.x**)
* **Package Managers**: `pip` (Python) and `npm` (Node.js)

---

## 2. Dependency Installation Steps

Open a terminal at the project root directory (`d:\pythonenginecrm`):

### Step A: Set up Python Virtual Environment
* **PowerShell**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
* **Command Prompt (CMD)**:
  ```cmd
  python -m venv venv
  .\venv\Scripts\activate.bat
  ```

### Step B: Install Core Package & Backend Modules
With your virtual environment active, execute the following:

1. **Install `mfrecon` package** in editable mode:
   ```powershell
   pip install -e .
   ```
2. **Install FastAPI backend dependencies**:
   ```powershell
   cd mfrecon-ui/backend
   pip install -r requirements.txt
   cd ../..
   ```

### Step C: Install React Frontend Packages
Install the frontend node packages:
```powershell
cd mfrecon-ui/frontend
npm install
cd ../..
```

---

## 3. Running the Application Locally

To run the interactive system, you will need two separate terminal windows open with your virtual environment activated:

### Window 1: FastAPI Backend
Start the Uvicorn web server:
```powershell
# In root directory, with venv activated:
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --app-dir mfrecon-ui
```
*Note: On startup, the backend automatically generates synthetic XLSX/PDF test files in `mfrecon-ui/demo_data/` for immediate demo testing.*

### Window 2: React Frontend
Start the Vite development server:
```powershell
# Navigate to frontend and run:
cd mfrecon-ui/frontend
npm run dev
```

---

## 4. Operational URLs

* **Dashboard Web UI**: [http://localhost:5173/](http://localhost:5173/)
* **FastAPI Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Backend Health Check**: [http://127.0.0.1:8000/api/system/health](http://127.0.0.1:8000/api/system/health)

---

## 5. Running the Test Suite (Pytest)

With the virtual environment active, run tests from the root directory (`d:\pythonenginecrm`):

* **Run all tests** (183 tests):
  ```powershell
  python -m pytest
  ```
* **Run specific functional improvements tests**:
  ```powershell
  python -m pytest tests/test_functional_improvements.py
  ```

### Setting up VS Code Testing UI
1. Install the official **Python** extension (by Microsoft) in VS Code.
2. Open the Command Palette (`Ctrl + Shift + P`) and select `Python: Select Interpreter`. Select your virtual environment: `.\venv\Scripts\python.exe`.
3. Open the Command Palette, select `Python: Configure Tests`, choose **pytest**, and select the **Root directory** (`.`).
4. You can now run or debug tests directly using the beaker icon on the sidebar.

---

## 6. How to Reconcile Files

### Option A: Sandbox "Demo Mode" (Quick Validation)
1. Navigate to the dashboard at [http://localhost:5173/](http://localhost:5173/).
2. Select **Demo Mode** in the left sidebar.
3. Click the violet **Load Demo Data & Execute** button.
4. The dashboard will trigger and display the pipeline results.

### Option B: Custom Reconciliation
1. Navigate to **Upload Files** tab at [http://localhost:5173/](http://localhost:5173/).
2. Drop your master **CRM Master File** (Excel/CSV) into the CRM dropzone.
3. Drop mutual fund transaction reports (CAMS, KFintech, BSE, NSE, or CAS PDF) into the **Transaction Reports** zone.
4. Click **Run Reconciliation** to initiate. Output reports (.xlsx, .csv, .json) will be available for download once completed.

---

## 7. Common Troubleshooting & Fixes

### Issue: `Port 8000 is already in use` (Errno 10048)
* **Cause**: Another uvicorn or python server is still occupying port 8000.
* **Fix**: Terminate the background python processes using PowerShell:
  ```powershell
  Stop-Process -Name "python" -Force
  ```
  Or launch the backend on port `8001`:
  ```powershell
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --app-dir mfrecon-ui
  ```

### Issue: `ModuleNotFoundError: No module named 'mfrecon'`
* **Cause**: Root packages are not linked in python.
* **Fix**: Run `pip install -e .` from the root directory with the virtual environment active.
