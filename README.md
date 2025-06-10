# EmploLeaksGuardian

EmploLeaksGuardian is a lightweight Python tool that scans multiple platforms for leaked API keys or secrets. It demonstrates a pluggable architecture and includes basic implementations for GitHub, DockerHub, HuggingFace, NPM, PyPI, Reddit and Pastebin.

The tool ships with a list of over 200 regex patterns derived from the public database at [secrets.ninja](https://secrets.ninja/). These patterns cover a wide variety of API keys and tokens to improve detection accuracy.

It can optionally search specific employee accounts by username and also provides a modern web interface on `localhost:8000` for controlling scans and viewing results. The UI is styled with Bootstrap for a clean look.

## Usage

```
python3 emploleaks.py
```
The tool will prompt for a GitHub token which is required for GitHub API access.
If you skip the token or provide an invalid one, GitHub searches may return no
results and you will see a warning message.

Follow the prompts to perform a normal scan on a chosen platform or run full auto mode across all supported platforms. You can also enable employee account scanning when prompted. Results are displayed in a formatted table using `rich`, or you can launch the web interface from the menu.

To use the web interface separately, run:

```
python3 webapp.py
```

This implementation provides a basic framework. Each searcher can be extended or improved by customizing the logic in the `core/` directory.
