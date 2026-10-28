# Demo 1 — Zero-Touch First Deploy

**Story:** "I have a web app in GitHub and a fresh RHEL 9 VM. I will configure
AAP to provision the server and deploy the app — without ever SSH-ing into the
VM. Not once."

**Duration:** ~10-15 minutes live

---

## What You Need Open

| Tab / Window | What |
|---|---|
| Browser — AAP | Automation Controller dashboard |
| Browser — VM  | `http://rhel9.sjwnx.sandbox1063.opentlc.com/` (will show error initially — that is the point) |
| Browser — GitHub | The webapp repo (to show the code exists) |

---

## Pre-Demo Setup (do this before the audience arrives)

1. Push the `webapp/` folder as its own GitHub repo (e.g. `github.com/<YOU>/demo-webapp`)
2. Push the `aap-automation/` folder as its own GitHub repo (e.g. `github.com/<YOU>/aap-automation`)
3. Ensure the RHEL 9 VM (`rhel9.sjwnx.sandbox1063.opentlc.com`) is freshly provisioned and reachable via SSH from the AAP Controller
4. Ensure you have SSH credentials (key-based) for `lab-user` on the VM

---

## Demo Script

### Step 1 — Set the scene

> **Say:** "Here is our situation. We have a developer's web application in
> GitHub — a Python Flask app with tests. And we have a brand new RHEL 9 VM
> that has never been touched. Let me show you."

**Action:** Show the webapp GitHub repo. Show `http://rhel9.sjwnx.sandbox1063.opentlc.com/`
returning an error (nothing is installed yet).

---

### Step 2 — Add Credentials

> **Say:** "First, I give AAP the credentials to talk to the VM and to pull
> code from GitHub. This is a one-time setup."

**Action in Automation Controller:**

1. Go to **Resources --> Credentials --> Add**
2. Create **Machine Credential**:
   - Name: `RHEL 9 Demo VM`
   - Credential Type: Machine
   - Username: `lab-user`
   - SSH Private Key: paste your private key
   - Privilege Escalation Method: sudo
   - Click **Save**
3. Create **Source Control Credential** (if repos are private):
   - Name: `GitHub SCM`
   - Credential Type: Source Control
   - Username: your GitHub username
   - Password / Token: paste GitHub PAT
   - Click **Save**

---

### Step 3 — Create the Automation Project

> **Say:** "Now I point AAP to our automation code repository. This is where
> our playbooks and templates live."

**Action:**

1. Go to **Resources --> Projects --> Add**
2. Fill in:
   - Name: `AAP Automation`
   - Source Control Type: Git
   - Source Control URL: `https://github.com/<YOU>/aap-automation.git`
   - Source Control Credential: `GitHub SCM` (if private)
   - Options: check **Update Revision on Launch**
3. Click **Save**
4. Wait for the sync to complete (green checkmark)

> **Say:** "AAP has synced our automation repo. It can now see our playbooks."

---

### Step 4 — Create the Inventory

> **Say:** "Next I tell AAP about our target VM. Just the FQDN and
> which user to connect as."

**Action:**

1. Go to **Resources --> Inventories --> Add --> Add Inventory**
2. Name: `Demo Inventory`, click **Save**
3. Go to the **Hosts** tab --> **Add**:
   - Name: `rhel9-demo`
   - Variables:
     ```yaml
     ansible_host: rhel9.sjwnx.sandbox1063.opentlc.com
     ansible_user: lab-user
     ```
   - Click **Save**
4. Go to **Groups** tab --> **Add**:
   - Name: `webservers`
   - Click **Save**, then go into the group and add `rhel9-demo` to it

---

### Step 5 — Create the Job Templates

> **Say:** "Now I create two job templates — one to provision the server,
> one to deploy the app."

**Action — Job Template 1 (Setup):**

1. Go to **Resources --> Templates --> Add --> Add Job Template**
2. Fill in:
   - Name: `Setup Web Server`
   - Job Type: Run
   - Inventory: `Demo Inventory`
   - Project: `AAP Automation`
   - Playbook: `playbooks/setup-webserver.yml`
   - Credentials: `RHEL 9 Demo VM`
3. Click **Save**

**Action — Job Template 2 (Deploy):**

1. Go to **Resources --> Templates --> Add --> Add Job Template**
2. Fill in:
   - Name: `Deploy Web App`
   - Job Type: Run
   - Inventory: `Demo Inventory`
   - Project: `AAP Automation`
   - Playbook: `playbooks/deploy-webapp.yml`
   - Credentials: `RHEL 9 Demo VM`
   - Extra Variables: enable **Prompt on launch**
3. Click **Save**

---

### Step 6 — Create a Workflow Template (the "wow" moment setup)

> **Say:** "Now here is where it gets powerful. I chain these two templates
> into a single workflow — setup the server, then deploy the app. One click."

**Action:**

1. Go to **Resources --> Templates --> Add --> Add Workflow Template**
2. Name: `Provision & Deploy`, click **Save**
3. Click **Visualizer** tab
4. Click **Start**, select `Setup Web Server`, click **Save**
5. Hover over the `Setup Web Server` node, click the **+** (on success)
6. Select `Deploy Web App`, click **Save** (in the prompt, set extra vars):
   ```yaml
   repo_url: https://github.com/<YOU>/demo-webapp.git
   commit_sha: main
   committer: admin
   ```
7. Click **Save** on the visualizer

> **Point out** the visual workflow graph to the audience — setup flows into
> deploy.

---

### Step 7 — Launch! (the "wow" moment)

> **Say:** "Let's do it. One click. Remember — I have never SSH-ed into this
> VM. It is a blank RHEL 9 machine."

**Action:**

1. Click **Launch** on the `Provision & Deploy` workflow template
2. Watch the workflow execute:
   - `Setup Web Server` runs: installs httpd, Python 3, creates the app user,
     configures the reverse proxy, opens the firewall
   - `Deploy Web App` runs: clones the webapp repo, installs Python deps,
     starts Gunicorn, verifies the health check

3. **While it runs**, narrate what each task is doing. The audience can see
   the real-time output in the Controller UI.

4. When the workflow completes (green checkmark), switch to the browser tab
   showing `http://rhel9.sjwnx.sandbox1063.opentlc.com/`

5. **Refresh the page.** The web app is live.

> **Say:** "From a blank VM to a running, tested, production-ready web
> application — without ever logging into the server. That is the power of
> Ansible Automation Platform."

---

## Key Talking Points

| Point | What to say |
|---|---|
| **Zero SSH** | "We never touched the terminal. No SSH, no manual commands." |
| **Repeatable** | "If I spin up 10 more VMs, I run the same workflow. Identical result every time." |
| **Auditable** | "Every task, every change is logged right here in the Controller. Full audit trail." |
| **Role-based** | "I can give a developer permission to launch this workflow without giving them SSH access to the VM." |
| **Idempotent** | "If I run this again, nothing breaks. Ansible only changes what needs changing." |

---

## What Just Happened (Technical Summary)

```
Workflow Template: "Provision & Deploy"
  |
  +--> Job 1: Setup Web Server (setup-webserver.yml)
  |      - dnf install httpd, python3, git
  |      - Create aap-demo system user
  |      - Configure httpd reverse proxy --> Gunicorn (127.0.0.1:8080)
  |      - SELinux: httpd_can_network_connect = on
  |      - Firewall: open port 80
  |
  +--> Job 2: Deploy Web App (deploy-webapp.yml)
         - git clone the webapp repo
         - python3 -m venv + pip install
         - Deploy Gunicorn systemd service
         - Health check: GET /health --> 200 OK
```

---

## Transition to Demo 2

> **Say:** "Now that the app is running, let's see what happens when the
> developer makes a change. In Demo 2, I will not even open the AAP portal.
> The entire deployment will be automatic — triggered by a git push."
