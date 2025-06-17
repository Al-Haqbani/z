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
    <title>EmploLeaksGuardian – Enterprise Secret Detection Platform</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css\" rel=\"stylesheet\">
    <link href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css\" rel=\"stylesheet\">
    <style>
      body { padding-top: 70px; }
      .scan-card { cursor: pointer; }
    </style>
  </head>
  <body class=\"bg-dark text-light\">
    <nav class=\"navbar navbar-expand-lg navbar-dark bg-primary fixed-top\">
      <div class=\"container\">
        <a class=\"navbar-brand fw-bold\" href=\"/\">EmploLeaksGuardian</a>
        <button class=\"navbar-toggler\" type=\"button\" data-bs-toggle=\"collapse\" data-bs-target=\"#nav\">
          <span class=\"navbar-toggler-icon\"></span>
        </button>
        <div id=\"nav\" class=\"collapse navbar-collapse\">
          <ul class=\"navbar-nav ms-auto\">
            <li class=\"nav-item\"><a class=\"nav-link\" href=\"/scans\">Scans</a></li>
          </ul>
        </div>
      </div>
    </nav>
    <div class=\"container\">
      <div class=\"text-center mb-4\">
        <i class=\"fa-solid fa-shield-halved fa-3x mb-2\"></i>
        <h1 class=\"display-5\">EmploLeaksGuardian – Enterprise Secret Detection Platform</h1>
      </div>
      <div class=\"row row-cols-1 row-cols-md-2 g-4 mb-4\">
        <div class=\"col\">
          <div class=\"card h-100 text-center scan-card\" data-mode=\"full\">
            <div class=\"card-body\">
              <h5 class=\"card-title\">Full Scan</h5>
              <p class=\"card-text\">Search all platforms with deep options.</p>
            </div>
          </div>
        </div>
        <div class=\"col\">
          <div class=\"card h-100 text-center scan-card\" data-mode=\"employees\">
            <div class=\"card-body\">
              <h5 class=\"card-title\">Employee Accounts</h5>
              <p class=\"card-text\">Include contributors when searching.</p>
            </div>
          </div>
        </div>
        <div class=\"col\">
          <div class=\"card h-100 text-center scan-card\" data-mode=\"packages\">
            <div class=\"card-body\">
              <h5 class=\"card-title\">Package Analysis</h5>
              <p class=\"card-text\">Check npm and PyPi packages.</p>
            </div>
          </div>
        </div>
        <div class=\"col\">
          <div class=\"card h-100 text-center scan-card\" data-mode=\"wayback\">
            <div class=\"card-body\">
              <h5 class=\"card-title\">Wayback Machine</h5>
              <p class=\"card-text\">Inspect archived repositories.</p>
            </div>
          </div>
        </div>
      </div>
      <form id=\"scanForm\" method=\"post\" action=\"/search\" class=\"bg-dark text-light p-4 rounded shadow-sm\">
        <ul class=\"nav nav-tabs mb-3\" id=\"scanTabs\" role=\"tablist\">
          <li class=\"nav-item\" role=\"presentation\">
            <button class=\"nav-link active\" id=\"tab-basic\" data-bs-toggle=\"tab\" data-bs-target=\"#basic\" type=\"button\" role=\"tab\">Basic Settings</button>
          </li>
          <li class=\"nav-item\" role=\"presentation\">
            <button class=\"nav-link\" id=\"tab-adv\" data-bs-toggle=\"tab\" data-bs-target=\"#advanced\" type=\"button\" role=\"tab\">Advanced Options</button>
          </li>
          <li class=\"nav-item\" role=\"presentation\">
            <button class=\"nav-link\" id=\"tab-sec\" data-bs-toggle=\"tab\" data-bs-target=\"#security\" type=\"button\" role=\"tab\">Security & Access</button>
          </li>
        </ul>
        <div class=\"tab-content\">
          <div class=\"tab-pane fade show active\" id=\"basic\" role=\"tabpanel\">
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
          </div>
          <div class=\"tab-pane fade\" id=\"advanced\" role=\"tabpanel\">
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
                <input class=\"form-check-input\" type=\"checkbox\" name=\"deep_scan\" id=\"deep_scan\">
                <label class=\"form-check-label\" for=\"deep_scan\">Deep Scan</label>
              </div>
              <div class=\"col-md-4 form-check\">
                <input class=\"form-check-input\" type=\"checkbox\" name=\"full_scan\" id=\"full_scan\">
                <label class=\"form-check-label\" for=\"full_scan\">Full Repo Scan</label>
              </div>
              <div class=\"col-md-4 form-check\">
                <input class=\"form-check-input\" type=\"checkbox\" name=\"scan_wayback\" id=\"scan_wayback\">
                <label class=\"form-check-label\" for=\"scan_wayback\">Wayback Repo</label>
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
          </div>
          <div class=\"tab-pane fade\" id=\"security\" role=\"tabpanel\">
            <div class=\"mb-3\">
              <label class=\"form-label\">Access Token</label>
              <input name=\"access_token\" class=\"form-control\">
            </div>
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
    <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js\"></script>
    <script>
      document.querySelectorAll('.scan-card').forEach(card=>{
        card.addEventListener('click',()=>{
          const mode=card.dataset.mode;
          if(mode==='full'){document.getElementById('full_scan').checked=true;}
          if(mode==='employees'){document.getElementById('use_emp').checked=true;}
          if(mode==='packages'){
             const n=document.getElementById('p_npm'); if(n) n.checked=true;
             const p=document.getElementById('p_pypi'); if(p) p.checked=true;
          }
          if(mode==='wayback'){document.getElementById('scan_wayback').checked=true;}
          document.getElementById('scanForm').scrollIntoView({behavior:'smooth'});
        });
      });
    </script>
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
    <link href=\"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css\" rel=\"stylesheet\">
    <link href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css\" rel=\"stylesheet\">
    <style>body { padding-top: 70px; }</style>
  </head>
  <body class=\"bg-dark text-light\">
    <nav class=\"navbar navbar-expand-lg navbar-dark bg-primary fixed-top\">
      <div class=\"container\">
        <a class=\"navbar-brand\" href=\"/\">EmploLeaksGuardian</a>
        <button class=\"navbar-toggler\" type=\"button\" data-bs-toggle=\"collapse\" data-bs-target=\"#nav2\">
          <span class=\"navbar-toggler-icon\"></span>
        </button>
        <div class=\"collapse navbar-collapse\" id=\"nav2\">
          <ul class=\"navbar-nav ms-auto\">
            <li class=\"nav-item\"><a class=\"nav-link\" href=\"/scans\">Scans</a></li>
          </ul>
        </div>
      </div>
    </nav>
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
    <link href=\"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css\" rel=\"stylesheet\">
    <link href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css\" rel=\"stylesheet\">
    <style>body { padding-top: 70px; }</style>
    <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
  </head>
  <body class=\"bg-dark text-light\">
    <nav class=\"navbar navbar-expand-lg navbar-dark bg-primary fixed-top\">
      <div class=\"container\">
        <a class=\"navbar-brand\" href=\"/\">EmploLeaksGuardian</a>
        <button class=\"navbar-toggler\" type=\"button\" data-bs-toggle=\"collapse\" data-bs-target=\"#nav3\">
          <span class=\"navbar-toggler-icon\"></span>
        </button>
        <div class=\"collapse navbar-collapse\" id=\"nav3\">
          <ul class=\"navbar-nav ms-auto\">
            <li class=\"nav-item\"><a class=\"nav-link\" href=\"/scans\">Scans</a></li>
          </ul>
        </div>
      </div>
    </nav>
    <div class=\"container\">
      <h1 class=\"mb-4\">Live Results for {{ keyword }}</h1>
      <div class="mb-3">
        <span class="badge bg-danger me-1">High <span id="count-high">0</span></span>
        <span class="badge bg-warning text-dark me-1">Medium <span id="count-medium">0</span></span>
        <span class="badge bg-info text-dark me-1">Low <span id="count-low">0</span></span>
        <span class="badge bg-secondary me-1">Info <span id="count-info">0</span></span>
      </div>
      <div class="row mb-3">
        <div class="col-md-6"><input id="searchBox" class="form-control form-control-sm" placeholder="Filter keywords"></div>
        <div class="col-md-3">
          <select id="severityFilter" class="form-select form-select-sm">
            <option value="">All Severities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="info">Info</option>
          </select>
        </div>
        <div class="col-md-3"><input id="platformFilter" class="form-control form-control-sm" placeholder="Platform"></div>
      </div>
      <div class="table-responsive">
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
      <div class="row mb-3">
        <div class="col-md-6"><canvas id="sevChart"></canvas></div>
        <div class="col-md-6"><canvas id="platChart"></canvas></div>
      </div>
      <p id="progress" class="mt-3"></p>
      <p id="done" class="mt-3" style="display:none">Scan completed.</p>
      <a href=\"/\" class=\"btn btn-secondary mt-3\">Back</a>
    </div>
    <script>
      const evt = new EventSource('/stream/{{ scan_id }}');
      const tbody = document.querySelector('#results tbody');
      const counters = {high:0, medium:0, low:0, info:0};
      const countEls = {
        high: document.getElementById('count-high'),
        medium: document.getElementById('count-medium'),
        low: document.getElementById('count-low'),
        info: document.getElementById('count-info')
      };
      const sevChart = new Chart(document.getElementById('sevChart'), {
        type: 'doughnut',
        data: { labels:['High','Medium','Low','Info'], datasets:[{ data:[0,0,0,0], backgroundColor:['#dc3545','#ffc107','#0dcaf0','#6c757d'] }] },
        options:{ plugins:{legend:{display:false}} }
      });
      const platChart = new Chart(document.getElementById('platChart'), {
        type: 'bar',
        data: { labels:[], datasets:[{ label:'Leaks', data:[], backgroundColor:'#6610f2' }] },
        options:{ scales:{y:{beginAtZero:true}} }
      });
      const platformCounts = {};
      const searchBox = document.getElementById('searchBox');
      const severityFilter = document.getElementById('severityFilter');
      const platformFilter = document.getElementById('platformFilter');

      function applyFilters() {
        const term = searchBox.value.toLowerCase();
        const sev = severityFilter.value;
        const plat = platformFilter.value.toLowerCase();
        tbody.querySelectorAll('tr').forEach(tr => {
          const matchesTerm = tr.textContent.toLowerCase().includes(term);
          const matchesSev = !sev || tr.dataset.sev === sev;
          const matchesPlat = !plat || tr.dataset.platform.toLowerCase().includes(plat);
          tr.style.display = matchesTerm && matchesSev && matchesPlat ? '' : 'none';
        });
      }

      searchBox.addEventListener('input', applyFilters);
      severityFilter.addEventListener('change', applyFilters);
      platformFilter.addEventListener('input', applyFilters);

      evt.addEventListener('message', ev => {
        const data = JSON.parse(ev.data);
        let sev = (data.severity || '').toLowerCase();
        if(!sev){
          sev = (data.leak_type || '').toLowerCase().includes('token') || (data.leak_type || '').toLowerCase().includes('key') ? 'high' : 'medium';
        }
        counters[sev] = (counters[sev] || 0) + 1;
        if(countEls[sev]) countEls[sev].innerText = counters[sev];
        sevChart.data.datasets[0].data = [counters.high, counters.medium, counters.low, counters.info];
        sevChart.update();
        const plat = data.source || 'Other';
        platformCounts[plat] = (platformCounts[plat] || 0) + 1;
        platChart.data.labels = Object.keys(platformCounts);
        platChart.data.datasets[0].data = Object.values(platformCounts);
        platChart.update();
        const row = document.createElement('tr');
        row.dataset.sev = sev;
        row.dataset.platform = data.source || '';
        row.className = sev === 'high' ? 'table-danger' : (sev === 'medium' ? 'table-warning' : 'table-light');
        const activeVal = data.active === null ? '?' : (data.active ? 'True' : 'False');
        row.innerHTML = `<td>${idx}</td><td>${data.source}</td><td><a href="${data.file}" target="_blank">${data.file}</a> <a href="${data.file}" target="_blank" class="ms-1 text-light"><i class="fa-solid fa-arrow-up-right-from-square"></i></a></td><td>${data.leak_type}</td><td><code>${data.value}</code> <button class="btn btn-sm btn-secondary ms-1 copy-btn" data-val="${data.value}"><i class="fa fa-copy"></i></button></td><td>${sev}</td><td>${activeVal}</td>`;
        tbody.appendChild(row);
        idx += 1;
        applyFilters();
      });

      evt.addEventListener('progress', ev => {
        const info = JSON.parse(ev.data);
        const msg = `Scanning ${info.repo} (${info.index}/${info.total})`;
        document.getElementById('progress').innerText = msg;
      });

      tbody.addEventListener('click', e => {
        const btn = e.target.closest('.copy-btn');
        if (btn) {
          navigator.clipboard.writeText(btn.dataset.val);
        }
      });

      evt.addEventListener('done', () => {
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
    <link href=\"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css\" rel=\"stylesheet\">
    <link href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css\" rel=\"stylesheet\">
    <style>body { padding-top: 70px; }</style>
  </head>
  <body class=\"bg-dark text-light\">
    <nav class=\"navbar navbar-expand-lg navbar-dark bg-primary fixed-top\">
      <div class=\"container\">
        <a class=\"navbar-brand\" href=\"/\">EmploLeaksGuardian</a>
        <button class=\"navbar-toggler\" type=\"button\" data-bs-toggle=\"collapse\" data-bs-target=\"#nav4\">
          <span class=\"navbar-toggler-icon\"></span>
        </button>
        <div class=\"collapse navbar-collapse\" id=\"nav4\">
          <ul class=\"navbar-nav ms-auto\">
            <li class=\"nav-item\"><a class=\"nav-link\" href=\"/scans\">Scans</a></li>
          </ul>
        </div>
      </div>
    </nav>
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
@app.route("/scans/")
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

    def progress(info):
        info["_event"] = "progress"
        q.put(info)

    def worker():
        if set(chosen) == set(SearchManager.PLATFORM_MAP.keys()):
            SearchManager.run_full_auto_mode(
                keyword,
                employees=employees if use_emp else None,
                verify_ai=verify_ai,
                full_scan=full_scan,
                scan_wayback=scan_wayback,
                result_callback=callback,
                progress_callback=progress,
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
                    progress_callback=progress,
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
            event = item.pop("_event", "message")
            yield f"event: {event}\ndata: {json.dumps(item)}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(port=8000, debug=True)
