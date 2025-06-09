# EmploLeaksGuardian

EmploLeaksGuardian is a lightweight Python tool that scans various platforms for leaked API keys or secrets. It demonstrates a pluggable architecture with placeholder implementations for multiple sources such as GitHub, DockerHub, and more.

## Downloading with Git

Clone the repository using:
```bash
git clone https://github.com/yourname/EmploLeaksGuardian.git
cd EmploLeaksGuardian/EmploLeaksGuardian8
```

## Usage

```
cd EmploLeaksGuardian8
python3 emploleaks.py
```

Follow the prompts to perform a normal scan or run full auto mode across all supported platforms. Results are displayed in a formatted table using `rich`.

To generate an HTML report and view it locally, use:

```
python3 generate_and_upload.py
```

This starts a small web server on `localhost:8000` so you can browse the report in your browser.

This implementation provides a basic framework and can be extended by filling in the search logic for additional platforms.
