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
        <tr><th>#</th><th>Source</th><th>File</th><th>Leak Type</th><th>Value</th><th>Severity</th><th>Active</th></tr>
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
        rows.append(
            f"        <tr class='{cls}'><td>{idx}</td><td>{item.get('source')}</td><td><a href='{item.get('file')}' target='_blank'>{item.get('file')}</a></td><td>{item.get('leak_type')}</td><td><code>{item.get('value')}</code></td><td>{sev}</td><td>{active_str}</td></tr>"
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
