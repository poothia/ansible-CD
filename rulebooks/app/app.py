"""
AAP Demo — Event-Driven CD Flask Application

A simple Flask web app deployed via Ansible Automation Platform.
Edit the template or config, push to GitHub, and watch it deploy automatically.
"""

import datetime
import os

from flask import Flask, render_template

app = Flask(__name__)

# ============================================================
# DEMO TIP: Change these values and push to trigger the pipeline!
# ============================================================
APP_VERSION = "1.0.0"
APP_TITLE = "Welcome to AAP Demo"
APP_SUBTITLE = "Event-Driven Continuous Deployment"
THEME_COLOR = "#ee0000"


@app.route("/")
def index():
    return render_template(
        "index.html",
        version=APP_VERSION,
        title=APP_TITLE,
        subtitle=APP_SUBTITLE,
        theme_color=THEME_COLOR,
        build_time=os.environ.get("BUILD_TIME", "unknown"),
        commit_sha=os.environ.get("COMMIT_SHA", "unknown"),
        hostname=os.environ.get("HOSTNAME", "localhost"),
    )


@app.route("/health")
def health():
    return {"status": "ok", "version": APP_VERSION, "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
