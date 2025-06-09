from datetime import datetime


def generate_html_report(results, path="report.html"):
    lines = ["<html><body>", f"<h1>EmploLeaksGuardian Report</h1>",
             f"<p>Generated: {datetime.utcnow()}</p>", "<table border='1'>",
             "<tr><th>#</th><th>Source</th><th>File</th><th>Leak Type</th><th>Value</th></tr>"]
    for idx, item in enumerate(results, 1):
        lines.append(
            f"<tr><td>{idx}</td><td>{item.get('source')}</td><td>{item.get('file')}</td><td>{item.get('leak_type')}</td><td>{item.get('value')}</td></tr>"
        )
    lines.append("</table></body></html>")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path
