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
    send_from_directory,
)
from core.search_manager import SearchManager
from core.token_manager import get_github_token

app = Flask(__name__)
# Tracks past and running scans keyed by an identifier.
# Each entry stores the keyword, results and current status.
SCAN_HISTORY = {}
# Queues used to stream results to the browser in real time.
SCAN_QUEUES = {}
# Sets controlling running scans
PAUSED_SCANS = set()
CANCELLED_SCANS = set()
# Recon specific history
RECON_HISTORY = {}
RECON_QUEUES = {}

INDEX_HTML = """
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>EmploLeaksGuardian – Enterprise Secret Detection Platform</title>
    <link rel=\"icon\" href=\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR4nGNgGAUAAQYBAqdo+gAAAABJRU5ErkJggg==\">
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
        <a class=\"navbar-brand fw-bold\" href=\"/\">
          <img src=\"/static/logo.svg\" alt=\"logo\" width=\"30\" class=\"me-2\">
          EmploLeaksGuardian
        </a>
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
                <input class=\"form-check-input\" type=\"checkbox\" name=\"scan_gists\" id=\"scan_gists\">
                <label class=\"form-check-label\" for=\"scan_gists\">Scan employee gists</label>
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
                <input class=\"form-check-input\" type=\"checkbox\" name=\"scan_releases\" id=\"scan_releases\">
                <label class=\"form-check-label\" for=\"scan_releases\">Scan Releases</label>
              </div>
              <div class=\"col-md-4 form-check\">
                <input class=\"form-check-input\" type=\"checkbox\" name=\"scan_actions\" id=\"scan_actions\">
                <label class=\"form-check-label\" for=\"scan_actions\">Scan Actions Logs</label>
              </div>
              <div class=\"col-md-4 form-check\">
                <input class=\"form-check-input\" type=\"checkbox\" name=\"verify_ai\" id=\"verify_ai\">
                <label class=\"form-check-label\" for=\"verify_ai\">Verify with AI</label>
              </div>
              <div class=\"col-md-4 form-check\">
                <input class=\"form-check-input\" type=\"checkbox\" name=\"active_verify\" id=\"active_verify\">
                <label class=\"form-check-label\" for=\"active_verify\">Verify leaks</label>
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
    <link rel=\"icon\" href=\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR4nGNgGAUAAQYBAqdo+gAAAABJRU5ErkJggg==\">
    <link href=\"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css\" rel=\"stylesheet\">
    <link href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css\" rel=\"stylesheet\">
    <style>body { padding-top: 70px; }</style>
  </head>
  <body class=\"bg-dark text-light\">
    <nav class=\"navbar navbar-expand-lg navbar-dark bg-primary fixed-top\">
      <div class=\"container\">
        <a class=\"navbar-brand\" href=\"/\">
          <img src=\"/static/logo.svg\" alt=\"logo\" width=\"30\" class=\"me-2\">
          EmploLeaksGuardian
        </a>
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
      <div class="form-check mb-2">
        <input class="form-check-input" type="checkbox" id="resVerifiedOnly">
        <label class="form-check-label" for="resVerifiedOnly">Show only verified leaks</label>
      </div>
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
      <script>
        const chk = document.getElementById('resVerifiedOnly');
        chk.addEventListener('change', ()=>{
          const showVerified = chk.checked;
          document.querySelectorAll('tbody tr').forEach(tr=>{
            const v = tr.children[6].textContent.trim() === 'True';
            tr.style.display = !showVerified || v ? '' : 'none';
          });
        });
      </script>
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
    <title>Live Dashboard</title>
    <link rel=\"icon\" href=\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR4nGNgGAUAAQYBAqdo+gAAAABJRU5ErkJggg==\">
    <link href=\"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css\" rel=\"stylesheet\">
    <link href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css\" rel=\"stylesheet\">
    <style>
      body { padding-top: 70px; }
      .sidebar { max-width: 260px; }
      @keyframes fadein { from {opacity:0;} to {opacity:1;} }
      tr.fade { animation: fadein 0.5s; }
    </style>
    <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
  </head>
  <body class=\"bg-dark text-light\">
    <nav class=\"navbar navbar-expand-lg navbar-dark bg-primary fixed-top\">
      <div class=\"container-fluid\">
        <a class=\"navbar-brand\" href=\"/\">
          <img src=\"/static/logo.svg\" alt=\"logo\" width=\"30\" class=\"me-2\">
          EmploLeaksGuardian
        </a>
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
    <div class=\"container-fluid\">
      <h1 class=\"mb-4\">Live Results for {{ keyword }}</h1>
      <div class=\"row\">
        <div class=\"col-md-3 sidebar\">
          <h5>Progress</h5>
          <div class=\"progress mb-3\">
            <div id=\"progBar\" class=\"progress-bar\" role=\"progressbar\" style=\"width:0%\"></div>
          </div>
          <p id=\"progressText\" class=\"small mb-3\"></p>
          <ul id=\"repoList\" class=\"list-group mb-3\"></ul>
          <ul class=\"list-group mb-3\">
            <li class=\"list-group-item bg-dark text-light d-flex justify-content-between align-items-center\">High<span class=\"badge bg-danger\" id=\"count-high\">0</span></li>
            <li class=\"list-group-item bg-dark text-light d-flex justify-content-between align-items-center\">Medium<span class=\"badge bg-warning text-dark\" id=\"count-medium\">0</span></li>
            <li class=\"list-group-item bg-dark text-light d-flex justify-content-between align-items-center\">Low<span class=\"badge bg-info text-dark\" id=\"count-low\">0</span></li>
            <li class=\"list-group-item bg-dark text-light d-flex justify-content-between align-items-center\">Info<span class=\"badge bg-secondary\" id=\"count-info\">0</span></li>
          </ul>
          <p class=\"small text-muted\">Total leaks: <span id=\"totalLeaks\">0</span></p>
          <canvas id=\"sevChart\" class=\"mb-4\"></canvas>
          <canvas id=\"platChart\"></canvas>
        </div>
        <div class=\"col-md-9\">
          <div class=\"row mb-3\">
            <div class=\"col-md-6\"><input id=\"searchBox\" class=\"form-control form-control-sm\" placeholder=\"Filter keywords\"></div>
            <div class=\"col-md-3\">
              <select id=\"severityFilter\" class=\"form-select form-select-sm\">
                <option value=\"\">All Severities</option>
                <option value=\"high\">High</option>
                <option value=\"medium\">Medium</option>
                <option value=\"low\">Low</option>
                <option value=\"info\">Info</option>
              </select>
            </div>
            <div class=\"col-md-3\"><input id=\"platformFilter\" class=\"form-control form-control-sm\" placeholder=\"Platform\"></div>
          </div>
          <div class=\"form-check mb-3\">
            <input class=\"form-check-input\" type=\"checkbox\" id=\"verifiedOnly\">
            <label class=\"form-check-label\" for=\"verifiedOnly\">Show only verified leaks</label>
          </div>
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
      </div>
    </div>
    <script>
      const evt = new EventSource('/stream/{{ scan_id }}');
      const tbody = document.querySelector('#results tbody');
      const counters = {high:0, medium:0, low:0, info:0};
      const platformCounts = {};
      const countEls = {
        high: document.getElementById('count-high'),
        medium: document.getElementById('count-medium'),
        low: document.getElementById('count-low'),
        info: document.getElementById('count-info')
      };
      const progBar = document.getElementById('progBar');
      const progText = document.getElementById('progressText');
      let leakTotal = 0;
      const repoList = document.getElementById('repoList');
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
      const searchBox = document.getElementById('searchBox');
      const severityFilter = document.getElementById('severityFilter');
      const platformFilter = document.getElementById('platformFilter');
      const verifiedOnly = document.getElementById('verifiedOnly');
      let idx = 1;
      const startTime = Date.now();
      setInterval(()=>{ progText.dataset.time = Math.floor((Date.now()-startTime)/1000); },1000);

      function applyFilters(){
        const term = searchBox.value.toLowerCase();
        const sev = severityFilter.value;
        const plat = platformFilter.value.toLowerCase();
        const needVerified = verifiedOnly.checked;
        tbody.querySelectorAll('tr').forEach(tr=>{
          const matchesTerm = tr.textContent.toLowerCase().includes(term);
          const matchesSev = !sev || tr.dataset.sev === sev;
          const matchesPlat = !plat || tr.dataset.platform.toLowerCase().includes(plat);
          const matchesVer = !needVerified || tr.dataset.verified === 'true';
          tr.style.display = matchesTerm && matchesSev && matchesPlat && matchesVer ? '' : 'none';
        });
      }
      searchBox.addEventListener('input',applyFilters);
      severityFilter.addEventListener('change',applyFilters);
      platformFilter.addEventListener('input',applyFilters);
      verifiedOnly.addEventListener('change',applyFilters);
      tbody.addEventListener('click',e=>{
        const btn=e.target.closest('.copy-btn');
        if(btn){navigator.clipboard.writeText(btn.dataset.val);}
      });
      evt.addEventListener('message',ev=>{
        const data=JSON.parse(ev.data);
        let sev=(data.severity||'').toLowerCase();
        if(!sev){sev=(data.leak_type||'').toLowerCase().includes('token')|| (data.leak_type||'').toLowerCase().includes('key')?'high':'medium';}
        counters[sev]=(counters[sev]||0)+1;
        if(countEls[sev]) countEls[sev].innerText=counters[sev];
        sevChart.data.datasets[0].data=[counters.high,counters.medium,counters.low,counters.info];
        sevChart.update();
        const plat=data.source||'Other';
        platformCounts[plat]=(platformCounts[plat]||0)+1;
        platChart.data.labels=Object.keys(platformCounts);
        platChart.data.datasets[0].data=Object.values(platformCounts);
        platChart.update();
        const row=document.createElement('tr');
        row.dataset.sev=sev; row.dataset.platform=plat; row.dataset.verified=data.active?'true':'false';
        row.className=(sev==='high'?'table-danger':(sev==='medium'?'table-warning':'table-light'))+' fade';
        const activeVal=data.active===null?'?':(data.active?'True':'False');
        row.innerHTML=`<td>${idx}</td><td>${data.source}</td><td><a href="${data.file}" target="_blank">${data.file}</a></td><td>${data.leak_type}</td><td><code>${data.value}</code> <button class="btn btn-sm btn-secondary ms-1 copy-btn" data-val="${data.value}"><i class="fa fa-copy"></i></button></td><td>${sev}</td><td>${activeVal}</td>`;
        tbody.appendChild(row); idx++; applyFilters();
      });
      evt.addEventListener('progress',ev=>{
        const info=JSON.parse(ev.data);
        if(info.status==='start'){
          const li=document.createElement('li');
          li.id='repo-'+info.repo.replace(/[^\w]+/g,'-');
          li.className='list-group-item list-group-item-dark';
          li.textContent=`Scanning ${info.repo}`;
          repoList.appendChild(li);
        }else if(info.status==='done'){
          const li=document.getElementById('repo-'+info.repo.replace(/[^\w]+/g,'-'));
          if(li){li.className='list-group-item list-group-item-success'; li.textContent=`${info.repo} done`;}
        }
        if(info.total){
          progText.textContent=`Scanning ${info.repo} (${info.index}/${info.total}) - ${progText.dataset.time||0}s`; 
          const pct=Math.round((info.index/info.total)*100);
          progBar.style.width=`${pct}%`;
        }
        if(info.leaks){
          leakTotal = info.leaks;
          document.getElementById('totalLeaks').innerText = leakTotal;
        }
      });
      evt.addEventListener('done',()=>{document.getElementById('done').style.display='block'; evt.close();});
    </script>
  </body>
</html>
"""

RECON_INDEX_HTML = """
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Recon Scanner</title>
    <link rel=\"icon\" href=\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR4nGNgGAUAAQYBAqdo+gAAAABJRU5ErkJggg==\">
    <link href=\"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css\" rel=\"stylesheet\">
  </head>
  <body class=\"bg-dark text-light\">
    <div class=\"container mt-4\">
      <h1 class=\"mb-4\">Recon Scanner</h1>
      <form method=\"post\" action=\"/recon_search\" class=\"mb-4\">
        <div class=\"mb-3\">
          <label class=\"form-label\">Keyword or Domain</label>
          <input class=\"form-control\" name=\"keyword\" required>
        </div>
        <button class=\"btn btn-primary\" type=\"submit\">Start Scan</button>
      </form>
      <h3 class=\"mt-4\">Previous Recon Scans</h3>
      <ul class=\"list-group\">
        {% for sid, item in history.items() %}
        <li class=\"list-group-item d-flex justify-content-between align-items-center\">
          <span>{{ item.keyword }}</span>
          <a href=\"/recon_live/{{sid}}\" class=\"btn btn-sm btn-outline-primary\">View</a>
        </li>
        {% endfor %}
      </ul>
    </div>
  </body>
</html>
"""

RECON_STREAM_HTML = """
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Recon Results</title>
    <link rel=\"icon\" href=\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR4nGNgGAUAAQYBAqdo+gAAAABJRU5ErkJggg==\">
    <link href=\"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css\" rel=\"stylesheet\">
    <style>body { padding-top: 20px; }</style>
  </head>
  <body class=\"bg-dark text-light\">
    <div class=\"container\">
      <h1 class=\"mb-4\">Recon Results for {{ keyword }}</h1>
      <div class=\"mb-3\">
        <input id=\"filter\" class=\"form-control form-control-sm\" placeholder=\"Filter\">
      </div>
      <div class=\"table-responsive\">
        <table class=\"table table-bordered table-striped\">
          <thead class=\"table-dark\"><tr><th>#</th><th>URL</th><th>Status</th><th>Source</th></tr></thead>
          <tbody id=\"tbody\"></tbody>
        </table>
      </div>
      <p id=\"done\" class=\"mt-3\" style=\"display:none\">Scan completed.</p>
      <a href=\"/recon\" class=\"btn btn-secondary mt-3\">Back</a>
    </div>
    <script>
      const tbody = document.getElementById('tbody');
      const filter = document.getElementById('filter');
      let idx=1;
      function apply() {
        const term = filter.value.toLowerCase();
        tbody.querySelectorAll('tr').forEach(tr=>{
          tr.style.display = tr.textContent.toLowerCase().includes(term) ? '' : 'none';
        });
      }
      filter.addEventListener('input', apply);
      const evt = new EventSource('/recon_stream/{{ scan_id }}');
      evt.onmessage = e => {
        const d = JSON.parse(e.data);
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${idx}</td><td><a href="${d.url}" target="_blank">${d.url}</a></td><td>${d.status}</td><td>${d.discovery}</td>`;
        tbody.appendChild(tr); idx++; apply();
      };
      evt.addEventListener('done', ()=>{document.getElementById('done').style.display='block';evt.close();});
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
    <link rel=\"icon\" href=\"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR4nGNgGAUAAQYBAqdo+gAAAABJRU5ErkJggg==\">
    <link href=\"https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/darkly/bootstrap.min.css\" rel=\"stylesheet\">
    <link href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css\" rel=\"stylesheet\">
    <style>body { padding-top: 70px; }</style>
  </head>
  <body class=\"bg-dark text-light\">
    <nav class=\"navbar navbar-expand-lg navbar-dark bg-primary fixed-top\">
      <div class=\"container\">
        <a class=\"navbar-brand\" href=\"/\">
          <img src=\"/static/logo.svg\" alt=\"logo\" width=\"30\" class=\"me-2\">
          EmploLeaksGuardian
        </a>
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

@app.route("/recon")
def recon_index():
    return render_template_string(
        RECON_INDEX_HTML,
        history=RECON_HISTORY,
    )

@app.route('/app/')
@app.route('/app/<path:path>')
def frontend(path='index.html'):
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend', 'build')
    return send_from_directory(frontend_dir, path)


@app.route("/scans")
@app.route("/scans/")
def scans():
    return render_template_string(
        SCANS_HTML,
        history=SCAN_HISTORY,
    )

@app.route("/api/scans")
def api_scans():
    return Response(json.dumps(SCAN_HISTORY), mimetype="application/json")

@app.route("/api/scan/<scan_id>/<action>", methods=["POST"])
def control_scan(scan_id, action):
    if action == "pause":
        PAUSED_SCANS.add(scan_id)
    elif action == "resume":
        PAUSED_SCANS.discard(scan_id)
    elif action == "cancel":
        CANCELLED_SCANS.add(scan_id)
        PAUSED_SCANS.discard(scan_id)
    return Response(json.dumps({"status": "ok"}), mimetype="application/json")


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
    scan_gists = request.form.get("scan_gists") == "on"
    deep_scan = request.form.get("deep_scan") == "on"
    full_scan = request.form.get("full_scan") == "on"
    scan_wayback = request.form.get("scan_wayback") == "on"
    scan_releases = request.form.get("scan_releases") == "on"
    scan_actions = request.form.get("scan_actions") == "on"
    verify_ai = request.form.get("verify_ai") == "on"
    active_verify = request.form.get("active_verify") == "on"
    silent = request.form.get("silent") == "on"
    chosen = request.form.getlist("platforms")
    if not chosen:
        chosen = list(SearchManager.PLATFORM_MAP.keys())
    tokens = {"github": gh_token, "gitlab": gl_token, "swaggerhub": swagger_token}
    kwargs = {
        "tokens": tokens,
        "scan_commits": scan_commits,
        "scan_gists": scan_gists,
        "silent": silent,
        "deep_scan": deep_scan,
        "scan_releases": scan_releases,
        "scan_actions": scan_actions,
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
        while scan_id in PAUSED_SCANS and scan_id not in CANCELLED_SCANS:
            time.sleep(0.5)
        if scan_id in CANCELLED_SCANS:
            raise RuntimeError("cancelled")
        info["_event"] = "progress"
        q.put(info)

    def worker():
        try:
            if set(chosen) == set(SearchManager.PLATFORM_MAP.keys()):
                SearchManager.run_full_auto_mode(
                    keyword,
                    employees=employees if use_emp else None,
                    verify_ai=verify_ai,
                    active_verify=active_verify,
                    full_scan=full_scan,
                    scan_wayback=scan_wayback,
                    scan_gists=scan_gists,
                    scan_releases=scan_releases,
                    scan_actions=scan_actions,
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
                        active_verify=active_verify,
                        full_scan=full_scan,
                    scan_wayback=scan_wayback,
                    scan_gists=scan_gists,
                    scan_releases=scan_releases,
                    scan_actions=scan_actions,
                    result_callback=callback,
                    progress_callback=progress,
                    **kwargs,
                )
        except RuntimeError:
            pass
        finally:
            q.put(None)
            if scan_id in SCAN_HISTORY:
                if scan_id in CANCELLED_SCANS:
                    SCAN_HISTORY[scan_id]["status"] = "cancelled"
                else:
                    SCAN_HISTORY[scan_id]["status"] = "done"
                from report_generator.generate_report import generate_html_report, save_json_report
                os.makedirs("reports", exist_ok=True)
                generate_html_report(results, path=f"reports/{scan_id}.html")
                save_json_report(results, path=f"reports/{scan_id}.json")

    threading.Thread(target=worker, daemon=True).start()

    return render_template_string(STREAM_HTML, keyword=keyword, scan_id=scan_id)


@app.route("/recon_search", methods=["POST"])
def recon_search():
    keyword = request.form.get("keyword", "")
    gh_token = os.environ.get("GITHUB_TOKEN")
    gl_token = os.environ.get("GITLAB_TOKEN")

    scan_id = str(int(time.time()))
    results = []
    q = queue.Queue()
    RECON_QUEUES[scan_id] = q
    RECON_HISTORY[scan_id] = {"keyword": keyword, "results": results, "status": "running"}

    def callback(item, idx):
        q.put({"url": item["file"], "status": item.get("status_code"), "discovery": item.get("discovery")})
        results.append(item)

    def worker():
        try:
            SearchManager.start_search(
                "recon",
                keyword,
                tokens={"github": gh_token, "gitlab": gl_token},
                result_callback=lambda item, idx: callback(item, idx),
            )
        finally:
            q.put(None)
            RECON_HISTORY[scan_id]["status"] = "done"
            os.makedirs("reports", exist_ok=True)
            from report_generator.generate_report import generate_html_report, save_json_report
            generate_html_report(results, path=f"reports/{scan_id}_recon.html")
            save_json_report(results, path=f"reports/{scan_id}_recon.json")

    threading.Thread(target=worker, daemon=True).start()

    return render_template_string(RECON_STREAM_HTML, keyword=keyword, scan_id=scan_id)


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

@app.route("/download/<path:filename>")
def download_report(filename):
    return send_from_directory("reports", filename, as_attachment=True)


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


@app.route("/recon_live/<scan_id>")
def recon_live(scan_id):
    scan = RECON_HISTORY.get(scan_id)
    if not scan:
        return "Not found", 404
    return render_template_string(
        RECON_STREAM_HTML,
        keyword=scan["keyword"],
        scan_id=scan_id,
    )


@app.route("/recon_stream/<scan_id>")
def recon_stream(scan_id):
    def event_stream():
        q = RECON_QUEUES.get(scan_id)
        if not q:
            yield "event: done\ndata: {}\n\n"
            return
        while True:
            item = q.get()
            if item is None:
                yield "event: done\ndata: {}\n\n"
                break
            yield f"data: {json.dumps(item)}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(port=8000, debug=True)
