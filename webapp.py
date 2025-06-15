import os
import time
import json
import queue
import threading
from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    Response,
)
from core.search_manager import SearchManager
from core.token_manager import get_github_token

app = Flask(__name__)
# Tracks past and running scans keyed by an identifier.
# Each entry stores the keyword, results and current status.
SCAN_HISTORY = {}
# Queues used to stream results to the browser in real time.
SCAN_QUEUES = {}

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
      <form method=\"post\" action=\"/search\" class=\"bg-white p-4 rounded shadow-sm mb-4\">
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
          <input name=\"github_token\" class=\"form-control\">
        </div>
        <div class=\"mb-3\">
          <label class=\"form-label\">GitLab Token</label>
          <input name=\"gitlab_token\" class=\"form-control\">
        </div>
        <div class=\"mb-3\">
          <label class=\"form-label\">SwaggerHub Token</label>
          <input name=\"swagger_token\" class=\"form-control\">
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
          <div class="col-md-4 form-check">
            <input class="form-check-input" type="checkbox" name="deep_scan" id="deep_scan">
            <label class="form-check-label" for="deep_scan">Deep Scan</label>
          </div>
          <div class="col-md-4 form-check">
            <input class="form-check-input" type="checkbox" name="full_scan" id="full_scan">
            <label class="form-check-label" for="full_scan">Full Repo Scan</label>
          </div>
          <div class="col-md-4 form-check">
            <input class="form-check-input" type="checkbox" name="scan_wayback" id="scan_wayback">
            <label class="form-check-label" for="scan_wayback">Wayback Repo</label>
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
      {% if history %}
      <h3 class=\"mt-4\">Recent Scans</h3>
      <ul class=\"list-group\">
        {% for sid, item in history.items() %}
        <li class=\"list-group-item d-flex justify-content-between align-items-center\">
          <span>{{ item.keyword }}</span>
          {% if item.status == 'running' %}
          <a class=\"btn btn-sm btn-outline-primary\" href=\"/live/{{sid}}\">Live</a>
          {% else %}
          <a class=\"btn btn-sm btn-outline-primary\" href=\"/results/{{sid}}\">View</a>
          {% endif %}
        </li>
        {% endfor %}
      </ul>
      <a href=\"/scans\" class=\"btn btn-link mt-2\">See all scans</a>
      {% endif %}
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
      <h1 class=\"mb-4\">Results for {{ keyword }}</h1>
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
              <th>Active</th>
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
              <td>{% if r.active is none %}?{% elif r.active %}True{% else %}False{% endif %}</td>
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

STREAM_HTML = """
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Live Results</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <style>body { padding-top: 40px; }</style>
  </head>
  <body class=\"bg-light\">
    <div class=\"container\">
      <h1 class=\"mb-4\">Live Results for {{ keyword }}</h1>
      <div class=\"table-responsive\">
        <table id=\"results\" class=\"table table-bordered table-striped\">
          <thead class=\"table-dark\">
            <tr>
              <th>#</th>
              <th>Source</th>
              <th>File</th>
              <th>Leak Type</th>
              <th>Value</th>
              <th>Severity</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
      <p id=\"done\" class=\"mt-3\" style=\"display:none\">Scan completed.</p>
      <a href=\"/\" class=\"btn btn-secondary mt-3\">Back</a>
    </div>
    <script>
      const evt = new EventSource('/stream/{{ scan_id }}');
      const tbody = document.querySelector('#results tbody');
      let idx = 1;
      evt.addEventListener('message', ev => {
        const data = JSON.parse(ev.data);
        const row = document.createElement('tr');
        const sev = data.severity || (data.leak_type.toLowerCase().includes('token') || data.leak_type.toLowerCase().includes('key') ? 'high' : 'medium');
        row.className = sev === 'high' ? 'table-danger' : (sev === 'medium' ? 'table-warning' : 'table-light');
        row.innerHTML = `<td>${idx}</td><td>${data.source}</td><td><a href="${data.file}" target="_blank">${data.file}</a></td><td>${data.leak_type}</td><td><code>${data.value}</code></td><td>${sev}</td><td>${data.active === null ? '?' : (data.active ? 'True' : 'False')}</td>`;
        tbody.appendChild(row);
        idx += 1;
      });
      evt.addEventListener('done', ev => {
        document.getElementById('done').style.display = 'block';
        evt.close();
      });
    </script>
  </body>
</html>
"""

SCANS_HTML = """
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Scans</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <style>body { padding-top: 40px; }</style>
  </head>
  <body class=\"bg-light\">
    <div class=\"container\">
      <h1 class=\"mb-4\">Scan History</h1>
      <div class=\"table-responsive\">
        <table class=\"table table-bordered\">
          <thead class=\"table-dark\">
            <tr>
              <th>Keyword</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
          {% for sid, item in history.items() %}
            <tr>
              <td>{{ item.keyword }}</td>
              <td>
                {% if item.status == 'running' %}
                <span class=\"badge bg-warning text-dark\">Running</span>
                {% else %}
                <span class=\"badge bg-success\">Done</span>
                {% endif %}
              </td>
              <td>
                {% if item.status == 'running' %}
                <a href=\"/live/{{sid}}\" class=\"btn btn-sm btn-outline-primary\">Live</a>
                {% else %}
                <a href=\"/results/{{sid}}\" class=\"btn btn-sm btn-outline-primary\">View</a>
                {% endif %}
              </td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
      <a href=\"/\" class=\"btn btn-secondary mt-3\">Back</a>
    </div>
  </body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        INDEX_HTML,
        platforms=SearchManager.PLATFORM_MAP.keys(),
        history=SCAN_HISTORY,
    )


@app.route("/scans")
def scans():
    return render_template_string(
        SCANS_HTML,
        history=SCAN_HISTORY,
    )


def _assign_severity(leak_type: str) -> str:
    name = leak_type.lower()
    if "token" in name or "key" in name:
        return "high"
    return "medium"

@app.route("/search", methods=["POST"])
def search():
    keyword = request.form.get("keyword", "")
    gh_token = request.form.get("github_token") or os.environ.get("GITHUB_TOKEN")
    gl_token = request.form.get("gitlab_token") or os.environ.get("GITLAB_TOKEN")
    swagger_token = request.form.get("swagger_token") or os.environ.get("SWAGGER_TOKEN")
    employees = request.form.get("employees")
    use_emp = request.form.get("use_employees") == "on"
    scan_commits = request.form.get("scan_commits") == "on"
    deep_scan = request.form.get("deep_scan") == "on"
    full_scan = request.form.get("full_scan") == "on"
    scan_wayback = request.form.get("scan_wayback") == "on"
    verify_ai = request.form.get("verify_ai") == "on"
    silent = request.form.get("silent") == "on"
    chosen = request.form.getlist("platforms")
    if not chosen:
        chosen = list(SearchManager.PLATFORM_MAP.keys())
    tokens = {"github": gh_token, "gitlab": gl_token, "swaggerhub": swagger_token}
    kwargs = {
        "tokens": tokens,
        "scan_commits": scan_commits,
        "silent": silent,
        "deep_scan": deep_scan,
        "full_scan": full_scan,
        "scan_wayback": scan_wayback,
    }

    scan_id = str(int(time.time()))
    results = []
    q = queue.Queue()
    SCAN_QUEUES[scan_id] = q
    # register scan as running so it appears immediately in history
    SCAN_HISTORY[scan_id] = {"keyword": keyword, "results": results, "status": "running"}

    def callback(item, idx):
        item.setdefault("severity", _assign_severity(item.get("leak_type", "")))
        q.put(item)
        results.append(item)

    def worker():
        if set(chosen) == set(SearchManager.PLATFORM_MAP.keys()):
            SearchManager.run_full_auto_mode(
                keyword,
                employees=employees if use_emp else None,
                verify_ai=verify_ai,
                full_scan=full_scan,
                scan_wayback=scan_wayback,
                result_callback=callback,
                **kwargs,
            )
        else:
            for platform in chosen:
                SearchManager.start_search(
                    platform,
                    keyword,
                    employees=employees if use_emp else None,
                    verify_ai=verify_ai,
                    full_scan=full_scan,
                    scan_wayback=scan_wayback,
                    result_callback=callback,
                    **kwargs,
                )
        q.put(None)
        if scan_id in SCAN_HISTORY:
            SCAN_HISTORY[scan_id]["status"] = "done"

    threading.Thread(target=worker, daemon=True).start()

    return render_template_string(STREAM_HTML, keyword=keyword, scan_id=scan_id)


@app.route("/results/<scan_id>")
def view_results(scan_id):
    scan = SCAN_HISTORY.get(scan_id)
    if not scan:
        return "Not found", 404
    if scan.get("status") != "done":
        # Redirect to live view if the scan is still running
        return redirect(url_for("live_results", scan_id=scan_id))
    return render_template_string(
        RESULTS_HTML,
        results=scan["results"],
        keyword=scan["keyword"],
    )


@app.route("/live/<scan_id>")
def live_results(scan_id):
    scan = SCAN_HISTORY.get(scan_id)
    if not scan:
        return "Not found", 404
    return render_template_string(
        STREAM_HTML,
        keyword=scan["keyword"],
        scan_id=scan_id,
    )


@app.route("/stream/<scan_id>")
def stream_results(scan_id):
    def event_stream():
        q = SCAN_QUEUES.get(scan_id)
        if not q:
            yield "event: done\ndata: {}\n\n"
            return
        while True:
            item = q.get()
            if item is None:
                if scan_id in SCAN_HISTORY:
                    SCAN_HISTORY[scan_id]["status"] = "done"
                yield "event: done\ndata: {}\n\n"
                break
            yield f"data: {json.dumps(item)}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(port=8000, debug=True)
