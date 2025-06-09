from report_generator.generate_report import generate_html_report
from web_server.serve_report import serve_report


def generate_and_upload(results, path="report.html", port=8000):
    """Generate the HTML report and serve it locally."""
    report = generate_html_report(results, path=path)
    serve_report(report, port=port)


if __name__ == "__main__":
    # Example usage
    sample = [{"source": "GitHub", "file": "example.py", "leak_type": "Token", "value": "ghp_xxx"}]
    generate_and_upload(sample)
