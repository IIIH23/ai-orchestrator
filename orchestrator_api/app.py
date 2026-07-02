"""Minimal operational API for AI Orchestrator."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify


SERVICE_NAME = "ai-orchestrator"
VERSION = "0.1.0"
PROJECTS_DIR = Path(__file__).resolve().parents[1] / "projects"


def _project_ids() -> list[str]:
    if not PROJECTS_DIR.is_dir():
        return []
    return sorted(path.stem for path in PROJECTS_DIR.glob("*.yaml"))


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": SERVICE_NAME,
                "version": VERSION,
                "environment": os.getenv("ORCHESTRATOR_ENV", "development"),
            }
        )

    @app.get("/version")
    def version():
        return jsonify({"service": SERVICE_NAME, "version": VERSION})

    @app.get("/v1/projects")
    def projects():
        project_ids = _project_ids()
        return jsonify({"projects": project_ids, "count": len(project_ids)})

    return app


if __name__ == "__main__":
    create_app().run(
        host="0.0.0.0",
        port=int(os.getenv("ORCHESTRATOR_PORT", "8080")),
    )
