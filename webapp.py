import os
from flask import Flask, render_template_string, request
from core.search_manager import SearchManager
from core.token_manager import get_github_token

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>EmploLeaksGuardian</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <style>
      body { padding-top: 40px; }
    </style>
  </head>
  <body class=\"bg-light\">
    <div class=\"container\">
      <div class=\"text-center mb-4\">
        <h1 class=\"display-5\">EmploLeaksGuardian</h1>
        <p class=\"lead\">Search multiple platforms for leaked secrets</p>
      </div>
      <form method=\"post\" action=\"/search\" class=\"bg-white p-4 rounded shadow-sm\">
        <div class=\"mb-3\">
          <label class=\"form-label\">Keyword</label>
          <input name=\"keyword\" class=\"form-control\" required>
        </div>
        <div class=\"mb-3\">
          <label class=\"form-label\">Employees (comma separated usernames)</label>
          <input name=\"employees\" class=\"form-control\">
        </div>
        <div class=\"mb-3\">
          <label class=\"form-label\">GitHub Token</label>
          <input name=\"token\" class=\"form-control\">
        </div>
        <div class=\"mb-3\">
          <label class=\"form-label\">Platforms</label>
          <div class=\"row\">
            {% for p in platforms %}
            <div class=\"col-6 col-md-4\">
              <div class=\"form-check\">
                <input class=\"form-check-input\" type=\"checkbox\" name=\"platforms\" value=\"{{p}}\" id=\"p_{{p}}\" checked>
                <label class=\"form-check-label\" for=\"p_{{p}}\">{{p}}</label>
              </div>
            </div>
            {% endfor %}
          </div>
        </div>
        <div class=\"form-check mb-2\">
          <input class=\"form-check-input\" type=\"checkbox\" name=\"use_employees\" id=\"use_emp\">
          <label class=\"form-check-label\" for=\"use_emp\">Search Employee Accounts</label>
        </div>
        <div class=\"row mb-3\">
          <div class=\"col-md-4 form-check\">
            <input class=\"form-check-input\" type=\"checkbox\" name=\"scan_commits\" id=\"scan_commits\">
            <label class=\"form-check-label\" for=\"scan_commits\">Scan Commits</label>
          </div>
          <div class=\"col-md-4 form-check\">
            <input class=\"form-check-input\" type=\"checkbox\" name=\"verify_ai\" id=\"verify_ai\">
            <label class=\"form-check-label\" for=\"verify_ai\">Verify with AI</label>
          </div>
          <div class=\"col-md-4 form-check\">
            <input class=\"form-check-input\" type=\"checkbox\" name=\"silent\" id=\"silent\">
            <label class=\"form-check-label\" for=\"silent\">Silent Mode</label>
          </div>
        </div>
        <button class=\"btn btn-primary\" type=\"submit\">Search</button>
      </form>
    </div>
  </body>
</html>
"""

RESULTS_HTML = """
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Results</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <style>
      body { padding-top: 40px; }
    </style>
  </head>
  <body class=\"bg-light\">
    <div class=\"container\">
      <h1 class=\"mb-4\">Results</h1>
      <p class=\"mb-3\"><strong>{{ results|length }} leaks found</strong></p>
      {% if results %}
      <div class=\"table-responsive\">
        <table class=\"table table-bordered table-striped\">
          <thead class=\"table-dark\">
            <tr>
              <th>#</th>
              <th>Source</th>
              <th>File</th>
              <th>Leak Type</th>
              <th>Value</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {% for idx, r in enumerate(results,1) %}
            <tr class="{% if r.severity=='high' %}table-danger{% elif r.severity=='medium' %}table-warning{% else %}table-light{% endif %}">
              <td>{{idx}}</td>
              <td>{{r.source}}</td>
              <td><a href="{{r.file}}" target="_blank">{{r.file}}</a></td>
              <td>{{r.leak_type}}</td>
              <td><code>{{r.value}}</code></td>
              <td>{{r.severity}}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
      {% else %}
      <p>No leaks found.</p>
      {% endif %}
      <a href="/" class=\"btn btn-secondary mt-3\">Back</a>
    </div>
  </body>
</html>
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
    scan_commits = request.form.get("scan_commits") == "on"
    verify_ai = request.form.get("verify_ai") == "on"
    silent = request.form.get("silent") == "on"
    chosen = request.form.getlist("platforms")
    results = []
    if not chosen:
        chosen = list(SearchManager.PLATFORM_MAP.keys())
    kwargs = {"token": token, "scan_commits": scan_commits, "silent": silent}
    if set(chosen) == set(SearchManager.PLATFORM_MAP.keys()):
        results = SearchManager.run_full_auto_mode(keyword, employees=employees if use_emp else None, verify_ai=verify_ai, **kwargs)
    else:
        for platform in chosen:
            results.extend(SearchManager.start_search(platform, keyword, employees=employees if use_emp else None, verify_ai=verify_ai, **kwargs))
    for r in results:
        r.setdefault("severity", _assign_severity(r.get("leak_type", "")))
    return render_template_string(RESULTS_HTML, results=results)


if __name__ == "__main__":
    app.run(port=8000, debug=True)
