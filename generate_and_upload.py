from report_generator.generate_report import generate_html_report, generate_pdf_report
from drive_upload.upload_to_drive import upload_to_drive


def generate_and_upload(results, path=None):
    """Generate an HTML report and upload it."""
    html = generate_html_report(results, path=path)
    pdf = generate_pdf_report(results, path=path.replace('.html', '.pdf') if path else None)
    upload_to_drive(html)
    upload_to_drive(pdf)


if __name__ == "__main__":
    # Example usage
    sample = [{"source": "GitHub", "file": "example.py", "leak_type": "Token", "value": "ghp_xxx"}]
    generate_and_upload(sample)
