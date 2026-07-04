# Installation Guide

This guide describes how to install and setup the **Mutual Fund Reconciliation Engine** package library in your Python environment.

---

## Prerequisites
Before installation, verify that you have:
* Python **3.12** or newer.
* `pip` package manager installed.
* Wheel compilation support (`pip install wheel`).

---

## Local Development Installation

If you are developing or modifying the package, clone the repository tree and install in editable mode:

```bash
# Navigate to the workspace directory containing pyproject.toml
cd pythonenginecrm

# Install the library locally along with required runtime packages
pip install -e .
```

---

## Production Installation

To build and distribute wheels or source distributions:

### 1. Build Package Artifacts
Ensure you have the Python build tools (`pip install build`) installed:

```bash
# Trigger wheel and sdist compilation
python -m build
```

This compiles:
* `dist/mfrecon-1.0.0-py3-none-any.whl` (Wheel format)
* `dist/mfrecon-1.0.0.tar.gz` (Source tarball)

### 2. Install Built Wheel
Install the compiled wheel in client environments:

```bash
pip install dist/mfrecon-1.0.0-py3-none-any.whl
```

---

## Verification
To verify the installation completed successfully:

```bash
# Check library registration
python -c "import mfrecon; print(mfrecon.__all__)"

# Execute CLI utility help command
mfrecon --help
```
