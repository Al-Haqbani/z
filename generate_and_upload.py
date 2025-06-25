from report_generator.generate_report import generate_html_report
from drive_upload.upload_to_drive import upload_to_drive


def generate_and_upload(results, path=None):
    """Generate an HTML report and upload it."""
    report = generate_html_report(results, path=path)
    upload_to_drive(report)


if __name__ == "__main__":
    # Example usage
    sample = [{"source": "GitHub", "file": "example.py", "leak_type": "Token", "value": "ghp_xxx"}]
    generate_and_upload(sample)
