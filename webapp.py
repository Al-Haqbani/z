import os
from flask import Flask, render_template_string, request
from core.search_manager import SearchManager
from core.token_manager import get_github_token

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<title>EmploLeaksGuardian</title>
<h1>EmploLeaksGuardian Search</h1>
<form method="post" action="/search">
Keyword: <input name="keyword" required><br>
Employees (comma separated usernames): <input name="employees"><br>
GitHub Token: <input name="token"><br>
Platforms:<br>
{% for p in platforms %}
  <label><input type="checkbox" name="platforms" value="{{p}}" checked> {{p}}</label><br>
{% endfor %}
<label><input type="checkbox" name="use_employees"> Search Employee Accounts</label><br>
<input type="submit" value="Search">
</form>
"""

RESULTS_HTML = """
<!doctype html>
<title>Results</title>
<h1>Results</h1>
<table border="1" cellpadding="5" cellspacing="0">
<tr><th>#</th><th>Source</th><th>File</th><th>Leak Type</th><th>Value</th><th>Severity</th></tr>
{% for idx, r in enumerate(results,1) %}
<tr style="background-color:{% if r.severity=='high' %}#ffcccc{% elif r.severity=='medium' %}#fff4cc{% else %}#f0f0f0{% endif %};">
<td>{{idx}}</td>
<td>{{r.source}}</td>
<td><a href="{{r.file}}" target="_blank">link</a></td>
<td>{{r.leak_type}}</td>
<td>{{r.value}}</td>
<td>{{r.severity}}</td>
</tr>
{% endfor %}
</table>
<a href="/">Back</a>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML, platforms=SearchManager.PLATFORM_MAP.keys())


def _assign_severity(leak_type: str) -> str:
    name = leak_type.lower()
    if "token" in name or "key" in name:
        return "high"
    return "medium"

@app.route("/search", methods=["POST"])
def search():
    keyword = request.form.get("keyword", "")
    token = request.form.get("token") or os.environ.get("GITHUB_TOKEN")
    employees = request.form.get("employees")
    use_emp = request.form.get("use_employees") == "on"
    chosen = request.form.getlist("platforms")
    results = []
    if not chosen:
        chosen = list(SearchManager.PLATFORM_MAP.keys())
    kwargs = {"token": token, "employees": employees if use_emp else None}
    if set(chosen) == set(SearchManager.PLATFORM_MAP.keys()):
        results = SearchManager.run_full_auto_mode(keyword, **kwargs)
    else:
        for platform in chosen:
            results.extend(SearchManager.start_search(platform, keyword, **kwargs))
    for r in results:
        r.setdefault("severity", _assign_severity(r.get("leak_type", "")))
    return render_template_string(RESULTS_HTML, results=results)


if __name__ == "__main__":
    app.run(port=8000, debug=True)
