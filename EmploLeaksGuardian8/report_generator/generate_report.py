from datetime import datetime


STYLE = """
<style>
body {font-family: Arial, Helvetica, sans-serif; background-color: #f5f7fa; color: #333; margin: 20px;}
h1 {color: #007acc;}
table {border-collapse: collapse; width: 100%;}
th, td {padding: 8px 12px; border-bottom: 1px solid #ddd;}
th {background-color: #007acc; color: #fff; text-align: left;}
tr:nth-child(even) {background-color: #f2f2f2;}
</style>
"""


def generate_html_report(results, path="report.html"):
    lines = [
        "<html>",
        "<head>",
        STYLE,
        "</head>",
        "<body>",
        f"<h1>EmploLeaksGuardian Report</h1>",
        f"<p>Generated: {datetime.utcnow()}</p>",
        "<table>",
        "<tr><th>#</th><th>Source</th><th>File</th><th>Leak Type</th><th>Value</th></tr>",
    ]
    for idx, item in enumerate(results, 1):
        lines.append(
            f"<tr><td>{idx}</td><td>{item.get('source')}</td><td>{item.get('file')}</td><td>{item.get('leak_type')}</td><td>{item.get('value')}</td></tr>"
        )
    lines.append("</table>")
    lines.append("</body></html>")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path
