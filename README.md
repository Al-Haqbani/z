# EmploLeaksGuardian

EmploLeaksGuardian is a lightweight Python tool that scans multiple platforms for leaked API keys or secrets. It now searches GitHub, **GitLab**, DockerHub, HuggingFace, NPM, PyPI, Reddit, Pastebin and **SwaggerHub** by performing real HTTP requests.

This project was originally created by **محمد الحقباني** to help security researchers uncover leaks and protect their organizations. The goal is to build the strongest global tool of its kind. Please use it responsibly for legitimate security testing only.
In addition, a **Smart JS Scanner** can crawl JavaScript files from any domain (including optional subdomains and archived copies via the Wayback Machine).

When commit scanning is enabled, GitHub results also include leaked secrets found in commit messages and diffs, allowing detection of tokens in deleted files.
An optional **Deep Scan** mode searches GitHub issues in addition to code and commits for more thorough coverage.

The tool ships with a list of over 200 regex patterns derived from the public database at [secrets.ninja](https://secrets.ninja/) and expanded with rules from [iwatchr.iscan.today](https://iwatchr.iscan.today/). These patterns cover a wide variety of API keys and tokens to improve detection accuracy. Additional generic patterns inspired by [Search for all leaked keys](https://github.com/Lu3ky13/Search-for-all-leaked-keys-secrets-using-one-regex-) help detect common password or API key assignments.
Recent updates also integrate private key signatures (RSA, DSA, EC and PGP) and JWT formats. All patterns are combined into a single master regex so scanning large files is much faster while still labeling each leak by type.

To further reduce false positives, matches are filtered using a small entropy check. Short or low‑entropy strings are ignored unless they resemble real credentials.

It can optionally search employees automatically by inspecting the contributors of a repository you provide. You can also search an entire GitHub organization in one go by supplying an org name. A modern web interface on `localhost:8000` lets you run scans and view results. The UI is styled with Bootstrap for a clean look and now lets you toggle AI verification, commit scanning and silent mode directly from your browser.
Full Auto Mode executes all searchers concurrently to accelerate large scans.
Leak results may also be verified by a free AI classifier. When enabled from the prompts or the web form, each detected token is checked with a lightweight model from HuggingFace to reduce false positives. For even more accuracy you can enable *active token verification*, which validates GitHub tokens directly via the API. Optional Telegram or Discord notifications can alert you when leaks are found.
The CLI now highlights the severity of each finding in color for quick triage.
When active verification is enabled, results now include an **Active** column indicating whether each token is still valid.

## Usage

```
python3 emploleaks.py
```
Install the dependencies first:

```
pip install -r requirements.txt
```

At startup you will be asked for API tokens for GitHub, GitLab and SwaggerHub.
Providing these tokens greatly improves the results on those platforms. If you
skip a token or provide an invalid one, searches on that platform may return no
results and you may see warning messages.

Follow the prompts to perform a normal scan on a chosen platform, run the Smart JS scan, or run full auto mode across all supported platforms. When employee scanning is enabled you will be asked for a repository name (owner/repo) and the tool will automatically gather contributor usernames. Results are displayed in a formatted table using `rich`. After each scan an HTML report named `results.html` is written with the complete links and color‑coded severity. You can also launch the web interface from the menu.

To use the web interface separately, run:

```
python3 webapp.py
```

AI verification requires the optional `transformers` and `torch` packages. Install them with:

```
pip install transformers torch
```

The main dependencies (listed in `requirements.txt`) are required to run the
scanner. The optional packages above are only needed if you enable the AI
verification feature from the prompts.

If you set the environment variables `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` or
`DISCORD_WEBHOOK_URL`, the tool can send alerts when leaks are discovered.

### Smart JS Scanner

The third menu option lets you scan a website's JavaScript files. You can choose
to enumerate subdomains, fetch archived files from the Wayback Machine and even
run [LinkFinder](https://github.com/GerbenJavado/LinkFinder) for deeper crawling.

```bash
python3 emploleaks.py
# choose "Smart JS Scan" from the menu
```

This implementation provides a basic framework. Each searcher can be extended or improved by customizing the logic in the `core/` directory. Support for **GitLab** and **SwaggerHub** has been added to broaden coverage across more platforms.

---

EmploLeaksGuardian is distributed for educational and defensive security purposes only. The author does **not** take responsibility for any misuse of this project.
