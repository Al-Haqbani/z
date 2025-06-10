# EmploLeaksGuardian

EmploLeaksGuardian is a lightweight Python tool that scans multiple platforms for leaked API keys or secrets. It demonstrates a pluggable architecture and includes basic implementations for GitHub, DockerHub, HuggingFace, NPM, PyPI, Reddit and Pastebin.

The tool ships with a list of over 200 regex patterns derived from the public database at [secrets.ninja](https://secrets.ninja/). These patterns cover a wide variety of API keys and tokens to improve detection accuracy.

It can optionally search employees automatically by inspecting the contributors of a repository you provide. A modern web interface on `localhost:8000` lets you run scans and view results. The UI is styled with Bootstrap for a clean look.
Leak results may also be verified by a free AI classifier. When enabled from the prompts, each detected token is checked with a lightweight model from HuggingFace to reduce false positives.

## Usage

```
python3 emploleaks.py
```
The tool will prompt for a GitHub token which is required for GitHub API access.
If you skip the token or provide an invalid one, GitHub searches may return no
results and you will see a warning message.

Follow the prompts to perform a normal scan on a chosen platform or run full auto mode across all supported platforms. When employee scanning is enabled you will be asked for a repository name (owner/repo) and the tool will automatically gather contributor usernames. Results are displayed in a formatted table using `rich`, or you can launch the web interface from the menu.

To use the web interface separately, run:

```
python3 webapp.py
```

AI verification requires the optional `transformers` and `torch` packages. Install them with:

```
pip install transformers torch
```

This implementation provides a basic framework. Each searcher can be extended or improved by customizing the logic in the `core/` directory.
