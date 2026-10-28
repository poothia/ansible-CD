# AAP Automation — Proof of Value Demo

Ansible playbooks, EDA rulebooks, and step-by-step demo guides for showcasing
**Ansible Automation Platform** to customers.

This repo is paired with a separate **webapp repo** (see `../webapp/`) that
contains a simple Flask application — the thing being deployed.

---

## Architecture

```
Demo 1: Zero-Touch First Deploy
================================
AAP Controller UI
  --> Workflow Template: "Provision & Deploy"
        --> Job 1: "Setup Web Server"    (setup-webserver.yml)
        --> Job 2: "Deploy Web App"      (deploy-webapp.yml)
              --> RHEL 9 VM is live

Demo 2: Hands-Off CD via EDA
================================
Developer pushes code
  --> GitHub Actions (build + test)
        --> Webhook POST to EDA Controller
              --> EDA rulebook matches event
                    --> Launches "Deploy Web App" job template
                          --> RHEL 9 VM is updated
```

---

## Target Environment

| Resource | Details |
|---|---|
| RHEL 9 VM | `rhel9.sjwnx.sandbox1063.opentlc.com` |
| SSH User | `lab-user` |
| Private IP | `192.168.0.81` (not used directly — access via FQDN) |

---

## What's in This Repo

| Path | Purpose |
|---|---|
| `playbooks/setup-webserver.yml` | Provisions a fresh RHEL 9 VM (httpd, Python 3, reverse proxy, firewall, SELinux) |
| `playbooks/deploy-webapp.yml` | Deploys the Flask app (git clone, virtualenv, Gunicorn, health check) |
| `playbooks/templates/*.j2` | Jinja2 templates for Gunicorn systemd service and httpd vhost |
| `rulebooks/github-webhook.yml` | EDA rulebook — listens for webhooks, triggers deploy job |
| `collections/requirements.yml` | Required Ansible collections (ansible.eda, ansible.posix) |
| `inventory/hosts.yml` | Reference inventory (actual inventory is in Automation Controller) |
| `group_vars/webservers.yml` | Variables for the webservers group |
| `DEMO-1-FIRST-DEPLOY.md` | Step-by-step guide for Demo 1 |
| `DEMO-2-EDA-CD.md` | Step-by-step guide for Demo 2 |

---

## Prerequisites

- **Ansible Automation Platform** with Automation Controller and EDA Controller
- RHEL 9 VM at `rhel9.sjwnx.sandbox1063.opentlc.com` reachable via SSH from the Controller
- **Two GitHub repos**: one for this automation code, one for the webapp
- Network path from GitHub to EDA Controller (public IP, reverse proxy, or ngrok)

---

## Demo Guides

### [Demo 1 — Zero-Touch First Deploy](DEMO-1-FIRST-DEPLOY.md)

Take a fresh RHEL 9 VM and deploy the web app entirely from the AAP portal —
without ever SSH-ing into the server.

**Shows:** Credentials, Projects, Inventories, Job Templates, Workflow Templates

### [Demo 2 — Hands-Off CD with EDA](DEMO-2-EDA-CD.md)

Change the app code, push to GitHub, and watch it deploy automatically — without
ever opening the AAP portal.

**Shows:** EDA Controller, Rulebook Activations, GitHub Actions integration,
event-driven automation

---

## Quick Reference — AAP Objects

### Automation Controller

| Object | Name | Details |
|---|---|---|
| Credential | `RHEL 9 Demo VM` | Machine type, `lab-user` + SSH key |
| Credential | `GitHub SCM` | Source Control type, GitHub PAT |
| Project | `AAP Automation` | Points to this repo |
| Inventory | `Demo Inventory` | Host `rhel9-demo` (`rhel9.sjwnx.sandbox1063.opentlc.com`) in group `webservers` |
| Job Template | `Setup Web Server` | Uses `playbooks/setup-webserver.yml` |
| Job Template | `Deploy Web App` | Uses `playbooks/deploy-webapp.yml`, extra vars on launch |
| Workflow Template | `Provision & Deploy` | Chains Setup --> Deploy (Demo 1) |

### EDA Controller

| Object | Name | Details |
|---|---|---|
| Credential | `AAP Controller Token` | Token to launch jobs on Automation Controller |
| Project | `AAP Automation` | Points to this repo (for rulebooks) |
| Rulebook Activation | `GitHub CD Webhook` | Activates `github-webhook.yml` |

### GitHub Secrets (on the webapp repo)

| Secret | Value |
|---|---|
| `EDA_WEBHOOK_URL` | EDA Controller webhook endpoint URL |
| `EDA_WEBHOOK_TOKEN` | Bearer token for webhook auth |

---

## Next Steps After the PoV

- Add **approval workflows** (approval node in the Controller workflow before deploy)
- Add **Slack / Teams notifications** on deploy success or failure
- Expand to **multi-environment** (dev --> staging --> prod) with separate inventories
- Add **ServiceNow integration** for automatic change tickets
- Add **monitoring events** (Dynatrace, Datadog) triggering auto-remediation via EDA
- Containerize the app and deploy to **OpenShift** via AAP
