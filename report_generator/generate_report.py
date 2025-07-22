from datetime import datetime
import json
import os


def _ensure_path(ext: str, path: str | None = None) -> str:
    """Return an output path using a timestamp if none is provided."""
    if path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        return path
    out_dir = os.environ.get("EMPLOLEAKS_OUTPUT", "reports")
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return os.path.join(out_dir, f"results_{timestamp}.{ext}")


def generate_html_report(results, path: str | None = None) -> str:
    """Write an HTML report with full links and severity color."""
    path = _ensure_path("html", path)

    head = f"""
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <title>EmploLeaksGuardian Report</title>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css' rel='stylesheet'>
</head>
<body class='container my-4'>
  <h1>EmploLeaksGuardian Report</h1>
  <p>Generated: {datetime.utcnow()}</p>
  <div class='table-responsive'>
    <table class='table table-bordered table-striped'>
      <thead class='table-dark'>
        <tr><th>#</th><th>Source</th><th>File</th><th>Leak Type</th><th>Value</th><th>Severity</th><th>Active</th><th>PoC</th><th>Screenshot</th></tr>
      </thead>
      <tbody>
"""

    rows = []
    for idx, item in enumerate(results, 1):
        sev = item.get("severity", "medium")
        cls = "table-danger" if sev == "high" else "table-warning" if sev == "medium" else "table-light"
        active = item.get('active')
        if active is None:
            active_str = '?' 
        else:
            active_str = 'True' if active else 'False'
        poc = item.get("poc", "")
        poc_html = f"<code>{poc}</code>" if poc else ""
        shot = item.get('screenshot')
        shot_html = f"<img src='{shot}' style=\"max-width:150px\">" if shot else ""
        rows.append(
            f"        <tr class='{cls}'><td>{idx}</td><td>{item.get('source')}</td><td><a href='{item.get('file')}' target='_blank'>{item.get('file')}</a></td><td>{item.get('leak_type')}</td><td><code>{item.get('value')}</code></td><td>{sev}</td><td>{active_str}</td><td>{poc_html}</td><td>{shot_html}</td></tr>"
        )

    tail = """
      </tbody>
    </table>
  </div>
</body>
</html>
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(rows) + tail)
    return path


def save_json_report(results, path: str | None = None) -> str:
    """Write results list to a JSON file."""
    path = _ensure_path("json", path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return path


def save_csv_report(results, path: str | None = None) -> str:
    """Write results to a CSV file."""
    import csv
    path = _ensure_path("csv", path)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Source", "File", "Leak Type", "Value", "Severity", "Active", "PoC"])
        for idx, item in enumerate(results, 1):
            active = item.get("active")
            if active is None:
                active_str = "?"
            else:
                active_str = "True" if active else "False"
            writer.writerow([
                idx,
                item.get("source", ""),
                item.get("file", ""),
                item.get("leak_type", ""),
                item.get("value", ""),
                item.get("severity", ""),
                active_str,
                item.get("poc", ""),
            ])
    return path


def generate_pdf_report(results, path: str | None = None) -> str:
    """Write a simple PDF report with leak table."""
    from fpdf import FPDF

    path = _ensure_path("pdf", path)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "EmploLeaksGuardian Report", ln=True)
    pdf.cell(0, 10, f"Generated: {datetime.utcnow()}", ln=True)
    pdf.ln(5)

    headers = ["#", "Source", "File", "Leak Type", "Value", "Severity", "Active"]
    col_widths = [10, 25, 65, 30, 40, 20, 15]
    pdf.set_font(style="B")
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 8, h, border=1)
    pdf.ln(8)
    pdf.set_font(style="")

    for idx, item in enumerate(results, 1):
        active = item.get("active")
        if active is None:
            active_str = "?"
        else:
            active_str = "True" if active else "False"
        row = [
            str(idx),
            item.get("source", ""),
            item.get("file", "")[:50],
            item.get("leak_type", ""),
            item.get("value", "")[:30],
            item.get("severity", ""),
            active_str,
        ]
        for text, w in zip(row, col_widths):
            pdf.cell(w, 8, text, border=1)
        pdf.ln(8)

    pdf.output(path)
    return path
