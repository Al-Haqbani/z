from datetime import datetime


def generate_html_report(results, path="report.html"):
    """Write an HTML report with full links and severity color."""

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
        <tr><th>#</th><th>Source</th><th>File</th><th>Leak Type</th><th>Value</th><th>Severity</th></tr>
      </thead>
      <tbody>
"""

    rows = []
    for idx, item in enumerate(results, 1):
        sev = item.get("severity", "medium")
        cls = "table-danger" if sev == "high" else "table-warning" if sev == "medium" else "table-light"
        rows.append(
            f"        <tr class='{cls}'><td>{idx}</td><td>{item.get('source')}</td><td><a href='{item.get('file')}' target='_blank'>{item.get('file')}</a></td><td>{item.get('leak_type')}</td><td><code>{item.get('value')}</code></td><td>{sev}</td></tr>"
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
