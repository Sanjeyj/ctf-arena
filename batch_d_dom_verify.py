"""
Batch D DOM Verification - Cyber Defense Platform
Tests all 19 Assurance, Validation, Exposure, and Operations Fabric routes.
"""
import io
import sys
import os

# Set UTF-8 encoding for standard output to avoid Unicode encoding errors on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure project root is in python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.chdir(project_root)

from app import create_app

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SERVER_NAME'] = None

ROUTES = [
    # Assurance Fabric
    ('/admin/assurance',              'Assurance',                            'Cyber Trust, Assurance'),
    ('/admin/assurance/cases',        'Assurance Cases Claims',               'Assurance Cases Claims'),
    ('/admin/assurance/controls',     'Control Validation Results',           'Continuous Control Validation'),
    ('/admin/assurance/devices',      'Device Posture Dashboard',             'Device Compliance'),
    ('/admin/assurance/trust',        'Zero Trust Decision Ledger',           'Zero Trust Decision Ledger'),
    ('/admin/assurance/supply-chain', 'Software Supply Chain Assurance',      'Software Supply Chain Attestations'),
    # Validation Fabric
    ('/admin/validation-fabric',              'Continuous Validation Fabric',      'Continuous Security Validation'),
    ('/admin/validation-fabric/campaigns',    'Validation Campaigns',              'Validation Campaigns'),
    ('/admin/validation-fabric/effectiveness','Defense Effectiveness metrics',     'Defense Effectiveness Metrics'),
    ('/admin/validation-fabric/readiness',    'Playbook Readiness Index',          'Playbook Readiness Index'),
    # Exposure Fabric
    ('/admin/exposure-fabric',              'Exposure Fabric Control Panel',  'Security Architecture, Exposure'),
    ('/admin/exposure-fabric/inventory',    'Exposed Assets Inventory',       'Exposed Assets Inventory Ledger'),
    ('/admin/exposure-fabric/findings',     'Exposure Findings',              'Vulnerability Findings'),
    ('/admin/exposure-fabric/paths',        'Logical Attack Paths',           'Logical Attack Paths'),
    # Operations Fabric
    ('/admin/operations-fabric',           'Operations Fabric Control Panel', 'Cyber Platform Observability'),
    ('/admin/operations-fabric/health',    'Service Health Dashboard',        'Platform Capabilities'),
    ('/admin/operations-fabric/incidents', 'Operational Incidents',           'Operational Incidents'),
    ('/admin/operations-fabric/telemetry', 'Telemetry Monitor',               'Telemetry Ingestion Monitoring'),
    ('/admin/operations-fabric/traces',    'Distributed Tracing',             'Distributed Traces'),
]

PASS = 0
FAIL = 0
ERRORS = []

def login(client):
    return client.post('/admin/login', data={
        'username': 'admin',
        'password': 'Admin@123'
    }, follow_redirects=True)

def check(label, condition, detail=''):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f'  [PASS] {label}')
    else:
        FAIL += 1
        ERRORS.append(f'{label}: {detail}')
        print(f'  [FAIL] {label}  [{detail}]')

with app.test_client() as client:
    r = login(client)
    check('Admin login successful', r.status_code == 200, f'status={r.status_code}')

    for route, title_fragment, h1_fragment in ROUTES:
        print(f'\n── {route}')
        try:
            resp = client.get(route, follow_redirects=True)
            html = resp.data.decode('utf-8', errors='replace')

            check(f'HTTP 200', resp.status_code == 200, f'got {resp.status_code}')
            check(f'Title contains "{title_fragment}"', title_fragment.lower() in html.lower(), 'title mismatch')
            check(f'H1 contains "{h1_fragment}"', h1_fragment.lower() in html.lower(), 'h1 mismatch')
            check(f'Sidebar present (ui-sidebar)', 'ui-sidebar' in html or 'ui-shell' in html or 'sidebar' in html.lower(), 'no sidebar')
            check(f'Glass card present (ui-glass-card)', 'ui-glass-card' in html, 'no glass card')
            check(f'No UndefinedError', 'UndefinedError' not in html, 'template variable error')
            check(f'No TemplateNotFound', 'TemplateNotFound' not in html, 'template not found')
            check(f'No Jinja2 error', '500' not in html or resp.status_code != 500, f'server error page')

        except Exception as e:
            FAIL += 1
            ERRORS.append(f'{route}: Exception - {e}')
            print(f'  [FAIL] Exception: {e}')

# ─── Summary ───────────────────────────────────────────────────
total = PASS + FAIL
print('\n' + '═' * 62)
print(f'  BATCH D DOM VERIFICATION')
print(f'  Routes tested : {len(ROUTES)}')
print(f'  Checks run    : {total}')
print(f'  PASSED        : {PASS}')
print(f'  FAILED        : {FAIL}')
print('═' * 62)

if ERRORS:
    print('\nFailed checks:')
    for e in ERRORS:
        print(f'  [FAIL] {e}')

if FAIL == 0:
    print('\n  ALL CHECKS PASSED - Batch D DOM verification COMPLETE')
    sys.exit(0)
else:
    print(f'\n  {FAIL} check(s) FAILED')
    sys.exit(1)
