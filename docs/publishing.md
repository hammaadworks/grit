# 🌍 Publishing & Deployment

Once you have built an awesome tool like Grit, you need to make it available so that any user on Earth can simply run `uv tool install grit` or `pip install grit`.

This page explains how to package, deploy, and publish Grit to PyPI (The Python Package Index).

---

## 1. Preparing for PyPI

Grit is configured using `pyproject.toml`. Before publishing a new version, ensure you have updated the metadata:

1. **Update the version number** in `pyproject.toml`:
   ```toml
   [project]
   name = "grit"
   version = "0.1.1" # <--- Bump this
   ```
2. **Ensure your README and License are ready**. PyPI uses your `README.md` as the landing page for your package.

---

## 2. Building the Package Locally

We use `uv build` (or the `build` module) to compile our Python code into distributable artifacts (a source archive `.tar.gz` and a built distribution `.whl`).

```bash
# Clean up any old builds
rm -rf dist/

# Build the wheels and source distribution
uv build
```
This will create a `dist/` directory containing the files ready to be uploaded to PyPI.

---

## 3. Publishing to PyPI (Manual Method)

To publish, you need an account on [PyPI](https://pypi.org/) and a generated API token.

You can use `uv publish` or `twine` to securely upload your package:

```bash
# Using uv (Requires uv 0.4.x+)
uv publish dist/* --token YOUR_PYPI_TOKEN

# Or using twine
uvx twine upload dist/*
```

!!! success "Available Worldwide"
    Once the upload finishes, anyone can install Grit using:
    ```bash
    uv tool install grit
    ```

---

## 4. Automated CI/CD Publishing (GitHub Actions)

The best way to deploy is to automate it. We have (or will set up) a GitHub Action that automatically publishes to PyPI whenever you push a new GitHub Release or tag.

### Setting up the Action
1. Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Add a new secret named `PYPI_TOKEN` containing your PyPI API token.
3. Create a `.github/workflows/publish.yml` file with the following content:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*.*.*' # Triggers on tags like v0.1.0

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Install uv
      uses: astral-sh/setup-uv@v3
      with:
        enable-cache: true
        
    - name: Build package
      run: uv build
      
    - name: Publish package
      run: uv publish --token ${{ secrets.PYPI_TOKEN }}

---

## 5. Commissioning Future Updates

Grit features a built-in update notification system to ensure users are always running the latest version.

### How the Update System Works
The `src/grit/updater.py` module is responsible for keeping users in the loop:
1.  **Check Interval**: Grit only checks for updates once every 24 hours to minimize network overhead.
2.  **Remote Verification**: It fetches the `pyproject.toml` from the main branch on GitHub to compare versions.
3.  **Environment Detection**: Grit detects if it was installed via `uv tool` or `pip` and provides the exact command needed to upgrade.
4.  **UI Integration**: The update banner is subtly displayed at the bottom of the `grit status` command.

### Releasing an Update
To "commission" an update to your users:
1.  **Bump Version**: Increment `version` in `pyproject.toml` and `__version__` in `src/grit/__init__.py`.
2.  **Tag & Push**: Create a new git tag (e.g., `git tag v0.2.0 && git push --tags`).
3.  **Deploy**: Once GitHub Actions publishes the new wheel to PyPI, users will start seeing the upgrade notice the next time they run `grit status`.
```

Now, whenever you run:
```bash
git tag v0.1.0
git push origin v0.1.0
```
GitHub Actions will automatically build and distribute your tool to the world!
