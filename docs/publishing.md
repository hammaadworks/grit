# 🌍 Publishing & Go-Live Guide

This guide explains how to package, deploy, and publish Grit to PyPI, along with a comprehensive checklist for every release.

---

## 1. Internal Testing & Build Sharing

Before going public, you should test the final "packaged" version of Grit to ensure the installation and entry points work as expected.

### Local "Final" Preview
To test exactly what a user will experience without publishing to PyPI:
1.  **Build the package**:
    ```bash
    rm -rf dist/
    uv build
    ```
2.  **Install the local wheel**:
    ```bash
    uv tool install ./dist/*.whl --force
    ```
3.  **Verify**: Run `grit status` or `grit --version` to ensure the global command points to your new build.

### Sharing with the Testing Team
If you want to share a build with internal testers before the public release:
*   **Share the Wheel**: Send the `.whl` file from the `dist/` folder to testers. They can install it using `pip install <path_to_file>.whl` or `uv tool install <path_to_file>.whl`.
*   **Test PyPI (Optional)**: For a truly realistic test, you can publish to [Test PyPI](https://test.pypi.org/):
    ```bash
    uv publish dist/* --publish-url https://test.pypi.org/legacy/ --token YOUR_TEST_PYPI_TOKEN
    ```
    Testers can then install via:
    ```bash
    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple grit
    ```

---

## 2. Preparing for Release

Grit is configured using `pyproject.toml`. Before publishing a new version, ensure you have updated the metadata:

1.  **Update the version number** in `pyproject.toml`:
    ```toml
    [project]
    version = "0.1.1" # <--- Bump this
    ```
2.  **Update `__init__.py`**: Ensure `src/grit/__init__.py` matches the new version.
3.  **Ensure your README and License are ready**. PyPI uses your `README.md` as the landing page for your package.

---

## 3. Building & Testing Locally

We use `uv build` to compile our Python code into distributable artifacts.

```bash
# Clean up any old builds
rm -rf dist/

# Build the wheels and source distribution
uv build
```

---

## 4. Publishing to PyPI

To publish, you need an account on [PyPI](https://pypi.org/) and a generated API token.

```bash
# Using uv (Requires uv 0.4.x+)
uv publish dist/* --token YOUR_PYPI_TOKEN
```

!!! success "Available Worldwide"
    Once the upload finishes, anyone can install Grit using:
    `uv tool install git2grit`

### 4.2 Using pip
```bash
pip install git2grit
```

---

## 5. Automated CI/CD (GitHub Actions)

The best way to deploy is to automate it via GitHub Actions whenever you push a new tag.

1.  Add `PYPI_TOKEN` to your GitHub Repository Secrets.
2.  Ensure `.github/workflows/publish.yml` is configured to trigger on tags like `v*.*.*`.

---

## 6. Website Deployment (GitHub Pages)

Grit's documentation and landing page are built with Next.js and deployed for free using **GitHub Pages**. 

We have configured an automated GitHub Action (`.github/workflows/deploy-docs.yml`) that builds and deploys the static export of the `website/` directory every time you push to the `master` branch.

!!! info "Automatic Deployment"
    The deployment process is **fully automatic**. Whether you change a core Python file in `src/` or a styling detail in `website/`, a push to `master` triggers the workflow. You don't need to run any manual commands to make your changes live on the web.

### Configuring Your Custom Domain
If you want to host the website on a custom domain (e.g., `grit.hammaadworks.com`), you need to configure your DNS records:

1. **GitHub Repository Settings**:
   - Go to your repository **Settings** -> **Pages**.
   - Under **Custom domain**, enter your domain (e.g., `grit.hammaadworks.com`) and click **Save**. This will automatically update the `CNAME` file in the repository.
   
2. **DNS Provider (e.g., Cloudflare, Namecheap, Route53)**:
   - Create a **CNAME record**.
   - **Name/Host**: `grit` (or whatever your subdomain is).
   - **Target/Value**: `hammaadworks.github.io`
   - *Note: GitHub Pages requires the target to be your GitHub username or organization name followed by `.github.io`.*

---

## 🚀 Go-Live Checklist

Follow these steps for every major and minor version update to ensure a smooth release.

### 🏗 Preparation
- [ ] **Run All Tests**: Ensure `pytest` passes with no failures.
- [ ] **Check Dependencies**: Ensure `uv.lock` is up-to-date.
- [ ] **Linting**: Ensure code adheres to standards.

### 🧪 Internal QA
- [ ] **Local Build**: Run `uv build`.
- [ ] **Local Install**: `uv tool install ./dist/*.whl --force`.
- [ ] **Smoke Test**: Run core commands (`config`, `commit`, `status`, `sync`).
- [ ] **Shared Testing**: (Optional) Share `.whl` with team or push to Test PyPI.

### 📝 Metadata & Documentation
- [ ] **Bump Version**: Update `pyproject.toml`, `src/grit/__init__.py`, and `website/src/lib/constants.ts`.
- [ ] **Changelog**: Summarize new features and fixes.
- [ ] **Docs Review**: Ensure `docs/` reflect all new commands.

### 📦 Distribution
- [ ] **Publish to PyPI**: `uv publish dist/ --token ...`.
- [ ] **Verify PyPI**: Ensure [pypi.org/project/git2grit](https://pypi.org/project/git2grit/) shows the new version.

### 🐙 Source Control
- [ ] **Git Tag**: `git tag vX.X.X && git push origin vX.X.X`.
- [ ] **GitHub Release**: Create a new release from the tag and attach the `dist/` files.

### 🌐 Website & Post-Launch
- [ ] **Deploy Website**: Ensure version and links on [grit.hammaadworks.com](https://grit.hammaadworks.com) are correct.
- [ ] **Public Verification**: Run `uv tool install git2grit` on a fresh machine.
