# EmploLeaksGuardian

EmploLeaksGuardian is a lightweight Python tool that scans multiple platforms for leaked API keys or secrets. It demonstrates a pluggable architecture and includes basic implementations for GitHub, DockerHub, HuggingFace, NPM, PyPI, Reddit and Pastebin.

## Usage

```
python3 emploleaks.py
```
The tool will prompt for a GitHub token which is required for GitHub API access.
If you skip the token or provide an invalid one, GitHub searches may return no
results and you will see a warning message.

Follow the prompts to perform a normal scan on a chosen platform or run full auto mode across all supported platforms. Results are displayed in a formatted table using `rich`.

This implementation provides a basic framework. Each searcher can be extended or improved by customizing the logic in the `core/` directory.
