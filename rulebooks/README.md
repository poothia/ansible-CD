# AAP Event-Driven CD Demo — Proof of Value

A complete **Build → Test → Deploy** pipeline using **Ansible Automation Platform (AAP)**.
Push a code change to a Flask web app, GitHub Actions builds and tests it, then
Event-Driven Ansible deploys it automatically to a RHEL VM — end to end.

## Architecture

```
Developer ──> GitHub ──> GitHub Actions ──────────> EDA Controller ──> Automation Controller ──> RHEL VM
  (git push)             (build + test + webhook)   (rulebook match)   (job template run)       (Flask app updated)
```

**Flow:**

1. Developer edits the Flask app (e.g. `app/app.py`) and pushes to `main`
2. GitHub Actions workflow fires (filtered to `app/**` changes)
3. GitHub Actions **builds** the app — installs Python deps, runs `pytest`
4. If tests pass, it **packages** the app as a tarball artifact
5. GitHub Actions sends a **webhook POST** to EDA Controller with commit metadata
6. EDA rulebook matches the event and **triggers** the "Deploy Web App" job template
7. Automation Controller runs the deploy playbook:
   - Clones the repo on the RHEL VM
   - Installs deps in a virtualenv
   - Restarts Gunicorn behind httpd reverse proxy
8. The web page updates live — visible in the browser

---

## Repository Structure

```
AAP_NSE/
├── .github/workflows/
│   └── notify-eda.yml                 # GitHub Actions: build, test, notify EDA
├── app/                                # Flask web application
│   ├── app.py                         # Main Flask app (change this during demo!)
│   ├── wsgi.py                        # WSGI entry point for Gunicorn
│   ├── config.py                      # App configuration
│   ├── requirements.txt               # Python dependencies
│   ├── templates/
│   │   └── index.html                 # Jinja2 template
│   ├── static/
│   │   └── style.css                  # Stylesheet
│   └── tests/
│       └── test_app.py                # Pytest tests
├── playbooks/
│   ├── deploy-webapp.yml              # Deploy playbook (triggered by EDA)
│   ├── setup-webserver.yml            # One-time server setup
│   └── templates/
│       ├── aap-demo.service.j2        # Gunicorn systemd service
│       └── aap-demo-httpd.conf.j2     # httpd reverse proxy config
├── rulebooks/
│   └── github-webhook.yml             # EDA rulebook
├── collections/
│   └── requirements.yml               # Required Ansible collections
├── group_vars/
│   └── webservers.yml                 # Web server variables
├── inventory/
│   └── hosts.yml                      # Reference inventory
└── README.md                          # This file
```

---

## The Web App

The demo app is a **Python Flask** application located in `app/`. It has:

- **`app.py`** — the main Flask app with configurable title, version, subtitle, and theme color (these are the values you change during the demo)
- **`templates/index.html`** — a Jinja2 template that renders a styled dashboard showing the pipeline stages, build metadata (commit SHA, build time, hostname), and Red Hat branding
- **`static/style.css`** — the stylesheet
- **`tests/test_app.py`** — pytest tests that verify the index page loads, contains the expected title/version, and the `/health` endpoint returns JSON
- **`wsgi.py`** — the WSGI entry point used by Gunicorn in production

### Running locally

```bash
cd app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# Open http://localhost:8080
```

### Running tests locally

```bash
cd app
python -m pytest tests/ -v
```

---

## Prerequisites

- **Ansible Automation Platform** with both **Automation Controller** and **EDA Controller** running
- A **RHEL VM** (accessible via SSH from Automation Controller)
- A **GitHub account** with a repository for this project
- Network connectivity: EDA Controller must be reachable from GitHub (public IP or tunnel)

---

## Setup Guide

### Step 1: Push this repo to GitHub

```bash
cd AAP_NSE
git add .
git commit -m "Initial commit - AAP EDA CD demo"
git remote add origin https://github.com/<YOUR_ORG>/AAP_NSE.git
git push -u origin main
```

### Step 2: Prepare the RHEL VM

Run the setup playbook once (either from Automation Controller or locally):

```bash
ansible-playbook -i inventory/hosts.yml playbooks/setup-webserver.yml
```

This will:
- Install httpd, Python 3, pip, and git
- Create an `aap-demo` system user
- Configure httpd as a reverse proxy to Gunicorn (port 8080)
- Set SELinux boolean for httpd network connect
- Open firewall port 80

### Step 3: Configure Automation Controller

#### 3a. Credentials

| Credential         | Type            | Details                                        |
|---------------------|-----------------|------------------------------------------------|
| **RHEL VM SSH**     | Machine         | SSH user + key for the RHEL VM                 |
| **GitHub SCM**      | Source Control   | GitHub PAT or deploy key for the repo          |

#### 3b. Project

1. Go to **Resources → Projects → Add**
2. **Name:** `AAP NSE Demo`
3. **Source Control Type:** Git
4. **Source Control URL:** `https://github.com/<YOUR_ORG>/AAP_NSE.git`
5. **Source Control Credential:** select your GitHub SCM credential
6. **Update Revision on Launch:** ✅ Enabled
7. Click **Save**

#### 3c. Inventory

1. Go to **Resources → Inventories → Add → Add Inventory**
2. **Name:** `Demo Inventory`
3. Click **Save**, then go to the **Hosts** tab
4. Click **Add** and create a host:
   - **Name:** `rhel-demo-vm`
   - **Variables:**
     ```yaml
     ansible_host: <YOUR_RHEL_VM_IP>
     ansible_user: <YOUR_SSH_USER>
     ```
5. Go to the **Groups** tab, create a group called `webservers`, and add the host to it

#### 3d. Job Template

1. Go to **Resources → Templates → Add → Add Job Template**
2. **Name:** `Deploy Web App`
3. **Job Type:** Run
4. **Inventory:** `Demo Inventory`
5. **Project:** `AAP NSE Demo`
6. **Playbook:** `playbooks/deploy-webapp.yml`
7. **Credentials:** select `RHEL VM SSH`
8. **Extra Variables:** enable **"Prompt on launch"** ✅
9. Click **Save**

### Step 4: Configure EDA Controller

#### 4a. Controller Token

1. In **Automation Controller**, go to **Users → admin → Tokens → Add**
2. Create a personal access token (PAT) — copy the token value
3. In **EDA Controller**, go to **User Credentials → Add**
   - **Name:** `AAP Controller Token`
   - **Credential Type:** Red Hat Ansible Automation Platform
   - **Token:** paste the token from step 2

#### 4b. EDA Project

1. Go to **Projects → Add**
2. **Name:** `AAP NSE Demo`
3. **SCM URL:** `https://github.com/<YOUR_ORG>/AAP_NSE.git`
4. **Credential:** select your GitHub SCM credential (if private repo)
5. Click **Save** and wait for sync

#### 4c. Rulebook Activation

1. Go to **Rulebook Activations → Add**
2. **Name:** `GitHub CD Webhook`
3. **Project:** `AAP NSE Demo`
4. **Rulebook:** `github-webhook.yml`
5. **Decision Environment:** Default Decision Environment
6. **Controller Credential:** `AAP Controller Token`
7. Click **Save**, then **Enable** the activation
8. Note the **webhook URL** — it will be:
   ```
   https://<EDA_CONTROLLER_HOST>:<PORT>/api/eda/v1/external_webhook/<ACTIVATION_ID>/
   ```

> **Tip:** If EDA Controller is behind a firewall, use a reverse proxy or ngrok to expose the webhook endpoint to GitHub.

### Step 5: Configure GitHub Secrets

1. Go to your GitHub repo → **Settings → Secrets and variables → Actions**
2. Add the following secrets:

| Secret Name          | Value                                              |
|-----------------------|----------------------------------------------------|
| `EDA_WEBHOOK_URL`    | The webhook URL from Step 4c                       |
| `EDA_WEBHOOK_TOKEN`  | The token used for webhook authentication (if any) |

---

## Running the Demo

### Pre-Demo Checklist

- [ ] RHEL VM is running and httpd is serving on port 80
- [ ] Run `setup-webserver.yml` has completed successfully
- [ ] Automation Controller: project synced, job template `Deploy Web App` exists
- [ ] EDA Controller: rulebook activation is **Enabled** (green status)
- [ ] GitHub secrets (`EDA_WEBHOOK_URL`, `EDA_WEBHOOK_TOKEN`) are configured
- [ ] Initial deploy has been run once (so the app is live)
- [ ] Browser tabs open: RHEL VM web page, GitHub Actions, EDA Controller, Automation Controller

### Demo Script

**1. Show the current state**
> Open the Flask app in a browser (`http://<RHEL_VM_IP>/`).
> Point out the version number, build time, and commit SHA displayed on the page.

**2. Show the code**
> Open `app/app.py` in your editor. Show that it's a real Python application
> with routes, templates, and tests — not just a static file.

**3. Make a visible change**
> Edit `app/app.py` — change the title, version, and theme color:
>
> ```python
> # Before
> APP_VERSION = "1.0.0"
> APP_TITLE = "Welcome to AAP Demo"
> APP_SUBTITLE = "Event-Driven Continuous Deployment"
> THEME_COLOR = "#ee0000"
>
> # After
> APP_VERSION = "2.0.0"
> APP_TITLE = "Deployed Live via AAP!"
> APP_SUBTITLE = "Build, Test & Deploy — Automated"
> THEME_COLOR = "#0066cc"
> ```

**4. Push the change**
```bash
git add app/app.py
git commit -m "v2.0 - updated live during demo"
git push
```

**5. Watch the pipeline**
> Switch between these tabs to show each stage:
>
> 1. **GitHub Actions** — the workflow runs:
>    - Python deps installed
>    - Tests pass ✅
>    - App packaged as tarball
>    - Webhook sent to EDA
> 2. **EDA Controller** — the event appears in the rulebook activation history
> 3. **Automation Controller** — the "Deploy Web App" job starts and completes:
>    - Clones repo at the new commit
>    - Installs deps in virtualenv
>    - Restarts Gunicorn
>    - Health check passes

**6. See the result**
> Refresh the browser showing the Flask app. The page now shows:
> - New title and blue theme color
> - Updated version number (2.0.0)
> - New commit SHA and build time

**7. Highlight the value**
> - End-to-end time: ~45-90 seconds from push to deploy
> - The app was **built and tested** before deployment — broken code won't deploy
> - Zero manual intervention
> - Full audit trail: Git commit → Build/Test → EDA event → Controller job
> - The `/health` endpoint confirms the app is running correctly

---

## Talking Points

| Customer Concern              | AAP Answer                                                              |
|-------------------------------|-------------------------------------------------------------------------|
| "We need faster deployments"  | Event-driven — builds, tests, and deploys in under 2 minutes            |
| "How do we prevent bad code?" | GitHub Actions runs tests; only passing builds trigger EDA              |
| "We need audit/compliance"    | Full traceability: commit SHA flows through build → EDA → deploy        |
| "We use GitHub already"       | AAP integrates with existing CI/CD — no rip and replace                 |
| "What about approvals?"       | Add approval nodes in Controller workflows before deploy                |
| "Can this scale?"             | AAP handles thousands of hosts; EDA processes events in real time       |
| "What about rollback?"        | Git revert + push triggers the same build/test/deploy pipeline          |

---

## Troubleshooting

| Issue                                    | Fix                                                              |
|------------------------------------------|------------------------------------------------------------------|
| GitHub Actions build fails               | Check `app/requirements.txt` and test output in Actions logs     |
| GitHub Actions webhook fails             | Check `EDA_WEBHOOK_URL` secret — ensure EDA is reachable        |
| EDA event not appearing                  | Check rulebook activation is enabled; check EDA controller logs  |
| Job template not launching               | Verify Controller Token credential in EDA; check token scope     |
| Playbook fails: "pip not found"          | Run `setup-webserver.yml` first to install Python 3              |
| App not responding after deploy          | Check Gunicorn: `systemctl status aap-demo`                      |
| httpd returns 503                        | Gunicorn may not be running; check SELinux: `setsebool -P httpd_can_network_connect 1` |
| Page not updating                        | Hard refresh browser (Ctrl+Shift+R); check `/health` endpoint   |

---

## Next Steps After the PoV

- Add **approval workflows** (Controller workflow with an approval node before deploy)
- Add **Slack/Teams notifications** on build failure or deploy success
- Expand to **multi-environment** (dev → staging → prod) with separate inventories
- Add **ServiceNow integration** for automatic change tickets
- Add **Dynatrace/Datadog** events triggering auto-remediation via EDA
- Containerize the app and deploy to **OpenShift** via AAP

---

## License

Internal use — Red Hat Proof of Value demo material.
