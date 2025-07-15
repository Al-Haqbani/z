from report_generator.generate_report import generate_html_report, generate_pdf_report
from drive_upload.upload_to_drive import upload_to_drive
from utils.json_tree import upload_json_tree


def generate_and_upload(results, path=None):
    """Generate an HTML/PDF report, upload it, and create a jsontr.ee link."""
    html = generate_html_report(results, path=path)
    pdf = generate_pdf_report(results, path=path.replace('.html', '.pdf') if path else None)
    upload_to_drive(html)
    upload_to_drive(pdf)
    try:
        link = upload_json_tree(results)
        print(f"jsontr.ee link: {link}")
    except Exception as exc:  # pragma: no cover - best effort
        print(f"jsontr.ee upload failed: {exc}")


if __name__ == "__main__":
    # Example usage
    sample = [{"source": "GitHub", "file": "example.py", "leak_type": "Token", "value": "ghp_xxx"}]
    generate_and_upload(sample)
