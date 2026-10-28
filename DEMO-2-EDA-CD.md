# Demo 2 — Hands-Off CD with Event-Driven Ansible

**Story:** "The app is live from Demo 1. Now I go back to being a developer.
I change the code, push to GitHub, and walk away. I never open the AAP portal.
GitHub Actions builds and tests the code, then Event-Driven Ansible
automatically deploys it. The page updates on its own."

**Duration:** ~10-12 minutes live (setup walkthrough + the live push)

---

## What You Need Open

| Tab / Window | What |
|---|---|
| Browser — AAP Controller | Jobs page (to watch the deploy job appear) |
| Browser — EDA Controller | Rulebook Activations page |
| Browser — GitHub Actions | The webapp repo's Actions tab |
| Browser — VM | `http://rhel9.sjwnx.sandbox1063.opentlc.com/` showing the live app (from Demo 1) |
| Editor | The webapp repo cloned locally, with `app.py` open |

---

## Pre-Demo Setup (do this before the audience arrives)

1. Demo 1 has been completed — the app is running on `rhel9.sjwnx.sandbox1063.opentlc.com`
2. The `aap-automation` repo is pushed to GitHub
3. The `webapp` repo is cloned locally on your laptop
4. You have access to the EDA Controller UI

---

## Demo Script

### Step 1 — Set the scene

> **Say:** "The app is running from our first demo. Now let's set up
> Event-Driven Ansible so that any code change automatically triggers a
> deployment — without anyone touching the AAP portal."

**Action:** Show the live app at `http://rhel9.sjwnx.sandbox1063.opentlc.com/`.
Point out the current version (1.0.0).

---

### Step 2 — Create the Controller Token

> **Say:** "First, EDA Controller needs permission to launch jobs on
> Automation Controller. I create a token for that."

**Action in Automation Controller:**

1. Go to **Users --> admin --> Tokens --> Add**
2. Scope: Write
3. Click **Save** and **copy the token value**

> **Say:** "This token lets EDA Controller talk to Automation Controller
> securely."

---

### Step 3 — Configure EDA Controller

> **Say:** "Now I configure three things in the EDA Controller — a credential,
> a project, and a rulebook activation."

#### 3a — Add the Controller Credential

1. In **EDA Controller**, go to **User Credentials --> Create credential**
2. Fill in:
   - Name: `AAP Controller Token`
   - Credential Type: Red Hat Ansible Automation Platform
   - Host: `https://<AUTOMATION_CONTROLLER_URL>`
   - Token: paste the token from Step 2
3. Click **Create credential**

#### 3b — Add the Automation Project

1. Go to **Projects --> Create project**
2. Fill in:
   - Name: `AAP Automation`
   - SCM Type: Git
   - SCM URL: `https://github.com/<YOU>/aap-automation.git`
   - Credential: `GitHub SCM` (if private)
3. Click **Create project**
4. Wait for sync to complete

> **Say:** "EDA now has access to our rulebook."

#### 3c — Create the Rulebook Activation

1. Go to **Rulebook Activations --> Create rulebook activation**
2. Fill in:
   - Name: `GitHub CD Webhook`
   - Project: `AAP Automation`
   - Rulebook: `github-webhook.yml`
   - Decision Environment: Default Decision Environment
   - Awx Token: `AAP Controller Token`
3. Click **Create rulebook activation**
4. Toggle the activation to **Enabled**

> **Say:** "The rulebook is now live. It's listening for webhook events."

5. Note the **webhook URL**. It will look like:
   ```
   https://<EDA_CONTROLLER_HOST>/api/eda/v1/external_webhook/<ACTIVATION_ID>/
   ```

> **Tip:** If EDA Controller is not publicly reachable from GitHub, set up
> ngrok or a reverse proxy before the demo and pre-configure the URL in
> GitHub Secrets.

---

### Step 4 — Show the Rulebook

> **Say:** "Let me show you what the rulebook looks like. It's simple YAML."

**Action:** Open `aap-automation/rulebooks/github-webhook.yml` and walk through
it:

```yaml
- name: Listen for GitHub CD events
  hosts: all
  sources:
    - ansible.eda.webhook:
        host: 0.0.0.0
        port: 5000
  rules:
    - name: Deploy on app change
      condition: event.payload.message == "App updated"
      action:
        run_job_template:
          name: "Deploy Web App"
          organization: "Default"
```

> **Say:** "Three parts — a source (webhook listener), a condition (match the
> event), and an action (launch the deploy job template). That's it."

---

### Step 5 — Configure GitHub Secrets

> **Say:** "Last piece — the webapp repo needs to know where to send the
> webhook."

**Action:**

1. Go to the webapp repo on GitHub --> **Settings --> Secrets and variables --> Actions**
2. Add two secrets:

   | Secret | Value |
   |---|---|
   | `EDA_WEBHOOK_URL` | The webhook URL from Step 3c |
   | `EDA_WEBHOOK_TOKEN` | The token for webhook auth (if configured) |

> **Say:** "Now the GitHub Actions workflow knows where to send the event
> after a successful build."

---

### Step 6 — Show the GitHub Actions Workflow

> **Say:** "Let me quickly show you the workflow file that's already in the
> webapp repo."

**Action:** Open `.github/workflows/notify-eda.yml` and highlight:

- Job 1: **Build & Test** — installs Python, runs pytest, packages the app
- Job 2: **Notify EDA** — only runs if tests pass, sends a curl POST to EDA

> **Say:** "Notice — if the tests fail, the webhook is never sent. Bad code
> does not get deployed. That's your safety net."

---

### Step 7 — The Live Push (the "wow" moment)

> **Say:** "Everything is wired up. Now let me be a developer. I'm going to
> change the app and push. I will not touch the AAP portal at all."

**Action:**

1. Open `app.py` in your editor. Change the highlighted constants:

   ```python
   # Before
   APP_VERSION = "1.0.0"
   APP_TITLE = "Welcome to the Demo App"
   THEME_COLOR = "#ee0000"

   # After
   APP_VERSION = "2.0.0"
   APP_TITLE = "Updated Live via EDA!"
   THEME_COLOR = "#0066cc"
   ```

2. Commit and push:

   ```bash
   git add app.py
   git commit -m "v2.0 - live update"
   git push
   ```

3. **Now narrate the chain as it happens** — switch between tabs:

   **Tab 1 — GitHub Actions:**
   > "The push triggered our CI workflow. It's installing dependencies...
   > running tests... tests passed. Now it's packaging the app and sending
   > the webhook to EDA."

   **Tab 2 — EDA Controller:**
   > "The event just arrived. The rulebook matched it — you can see the rule
   > 'Deploy on app change' fired. It's launching the job template on
   > Automation Controller."

   **Tab 3 — Automation Controller:**
   > "There it is — the 'Deploy Web App' job just started automatically.
   > Nobody clicked anything. It's pulling the new code, installing deps,
   > restarting the app... health check passed."

   **Tab 4 — VM Browser:**
   > "And now..." *refresh `http://rhel9.sjwnx.sandbox1063.opentlc.com/`*
   > "...the page is updated. New title, new color, new version. Deployed
   > automatically in about 60 seconds."

---

## Key Talking Points

| Point | What to say |
|---|---|
| **Developer freedom** | "The developer just pushes code. They don't need AAP access, don't need to know about playbooks." |
| **Tests are the gate** | "If tests fail, deployment does not happen. The webhook is only sent after a successful build." |
| **No AAP login needed** | "I did not open the AAP portal to deploy. The event-driven workflow handled everything." |
| **Full traceability** | "The commit SHA flows from GitHub --> GitHub Actions --> EDA --> Controller --> the running app. Full audit chain." |
| **Real-time** | "This is not polling on a schedule. The moment code is pushed, the pipeline fires." |
| **Extensible** | "I could add Slack notifications, approval gates, multi-environment deployments — all within AAP." |

---

## What Just Happened (Technical Summary)

```
Developer pushes to GitHub (main branch)
  |
  v
GitHub Actions: "Build, Test & Deploy via EDA"
  |
  +--> Job 1: Build & Test
  |      - pip install -r requirements.txt
  |      - pytest tests/ -v
  |      - tar czf webapp-<sha>.tar.gz ...
  |      - Upload artifact
  |
  +--> Job 2: Notify EDA (runs only if Job 1 passes)
         - curl POST --> EDA Controller webhook URL
         - Payload: { repo, commit_sha, committer, "App updated" }
           |
           v
EDA Controller: Rulebook "github-webhook.yml"
  - Source: ansible.eda.webhook (port 5000)
  - Condition: event.payload.message == "App updated"  --> MATCH
  - Action: run_job_template "Deploy Web App"
    |
    v
Automation Controller: Job Template "Deploy Web App"
  - extra_vars: repo_url, commit_sha, committer
  - Playbook: deploy-webapp.yml
    |
    v
RHEL 9 VM (rhel9.sjwnx.sandbox1063.opentlc.com):
  - git clone webapp repo @ commit_sha
  - pip install in virtualenv
  - Restart Gunicorn systemd service
  - Health check: GET /health --> 200 OK
  - App is live with new version
```

---

## Troubleshooting During Demo

| Problem | Quick Fix |
|---|---|
| GitHub Actions doesn't trigger | Check the branch is `main` and the changed file matches the path filter |
| Webhook returns HTTP error | Check `EDA_WEBHOOK_URL` secret is correct; verify EDA is reachable from GitHub |
| EDA event not showing | Check rulebook activation is enabled (green); check EDA logs |
| Controller job doesn't start | Verify the Controller Token has write scope; check EDA credential config |
| App not updating | Check Gunicorn service: `systemctl status aap-demo` (via Controller ad-hoc command) |

---

## Wrap-Up

> **Say:** "Let me recap what we just saw:
>
> In Demo 1, we took a blank RHEL 9 VM and deployed a web application
> from AAP — without ever SSH-ing into the server.
>
> In Demo 2, we changed the code and pushed. We never touched the AAP
> portal. GitHub Actions built and tested the code, Event-Driven Ansible
> picked up the event, and Automation Controller deployed the update.
>
> This is the power of Ansible Automation Platform — infrastructure
> provisioning, application deployment, and event-driven automation, all
> in one platform."
