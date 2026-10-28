# AAP Event-Driven CD Demo — Proof of Value

A complete **Continuous Deployment** demo using **Ansible Automation Platform (AAP)**.
Push a code change to GitHub and watch it deploy automatically to a RHEL VM — end to end.

## Architecture

```
Developer ──> GitHub ──> GitHub Actions ──> EDA Controller ──> Automation Controller ──> RHEL VM (httpd)
  (git push)             (webhook POST)     (rulebook match)   (job template run)       (page updated)
```

**Flow:**

1. Developer edits `app/index.html` and pushes to `main`
2. GitHub Actions workflow fires (filtered to `app/**` changes)
3. GitHub Actions sends a webhook POST to EDA Controller with commit metadata
4. EDA rulebook matches the event and triggers the "Deploy Web App" job template
5. Automation Controller runs the deploy playbook on the RHEL VM
6. The web page updates live — visible in the browser

---

## Repository Structure

```
AAP_NSE/
├── .github/workflows/
│   └── notify-eda.yml              # GitHub Actions → EDA webhook
├── app/
│   └── index.html                  # The web app (change this during demo)
├── playbooks/
│   ├── deploy-webapp.yml           # Deploy playbook (triggered by EDA)
│   └── setup-webserver.yml         # One-time httpd setup
├── rulebooks/
│   └── github-webhook.yml          # EDA rulebook
├── collections/
│   └── requirements.yml            # Required Ansible collections
├── group_vars/
│   └── webservers.yml              # Web server variables
├── inventory/
│   └── hosts.yml                   # Reference inventory
└── README.md                       # This file
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

This installs `httpd`, opens port 80, and places a placeholder page.

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
- [ ] Automation Controller: project synced, job template exists
- [ ] EDA Controller: rulebook activation is **Enabled** (green status)
- [ ] GitHub secrets are configured
- [ ] Browser tabs open: RHEL VM web page, GitHub Actions, EDA Controller, Automation Controller

### Demo Script

**1. Show the current state**
> Open the RHEL VM web page in a browser. Show the audience the current version.

**2. Make a visible change**
> Open `app/index.html` in your editor. Change the heading text:
> ```html
> <!-- Before -->
> <h1>Welcome to AAP Demo</h1>
> <p class="version">VERSION 1.0 — Initial Deployment</p>
>
> <!-- After -->
> <h1>Deployment v2.0 — Updated Live!</h1>
> <p class="version">VERSION 2.0 — Deployed via Event-Driven Ansible</p>
> ```

**3. Push the change**
```bash
git add app/index.html
git commit -m "Update landing page to v2.0"
git push
```

**4. Watch the pipeline**
> Switch between these tabs to show each stage firing:
> 1. **GitHub Actions** — the workflow runs and sends the webhook
> 2. **EDA Controller** — the event appears in the rulebook activation history
> 3. **Automation Controller** — the "Deploy Web App" job starts and completes

**5. See the result**
> Refresh the browser showing the RHEL VM web page. The updated heading is live!

**6. Highlight the value**
> - Total time: ~30-60 seconds from push to deploy
> - Zero manual intervention
> - Full audit trail: Git commit → GitHub Actions → EDA event → Controller job
> - Extensible: add approval gates, notifications, multi-stage deployments

---

## Talking Points

| Customer Concern              | AAP Answer                                                          |
|-------------------------------|---------------------------------------------------------------------|
| "We need faster deployments"  | Event-driven — deploys in seconds after push, not minutes/hours     |
| "We need audit/compliance"    | Full traceability: commit SHA flows through every stage             |
| "We use GitHub already"       | AAP integrates with existing CI/CD — no rip and replace             |
| "What about approvals?"       | Add approval nodes in Controller workflows before deploy            |
| "Can this scale?"             | AAP handles thousands of hosts; EDA processes events in real time   |
| "What about rollback?"        | Git revert + push triggers the same pipeline — instant rollback     |

---

## Troubleshooting

| Issue                                    | Fix                                                              |
|------------------------------------------|------------------------------------------------------------------|
| GitHub Actions fails with HTTP error     | Check `EDA_WEBHOOK_URL` secret — ensure EDA is reachable        |
| EDA event not appearing                  | Check rulebook activation is enabled; check EDA controller logs  |
| Job template not launching               | Verify Controller Token credential in EDA; check token scope     |
| Playbook fails on RHEL VM               | Ensure SSH connectivity; run setup-webserver.yml first           |
| Page not updating                        | Check httpd is running: `systemctl status httpd`                 |

---

## Next Steps After the PoV

- Add **approval workflows** (Controller workflow with an approval node)
- Add **Slack/Teams notifications** on deploy success/failure
- Expand to **multi-environment** (dev → staging → prod) with separate inventories
- Add **ServiceNow integration** for change tickets
- Add **Dynatrace/Datadog** events triggering auto-remediation via EDA

---

## License

Internal use — Red Hat Proof of Value demo material.
