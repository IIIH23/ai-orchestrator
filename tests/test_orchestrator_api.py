from orchestrator_api.app import SERVICE_NAME, VERSION, create_app


def test_health_reports_runtime_identity(monkeypatch) -> None:
    monkeypatch.setenv("ORCHESTRATOR_ENV", "test")
    client = create_app().test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": VERSION,
        "environment": "test",
    }


def test_version_is_stable() -> None:
    response = create_app().test_client().get("/version")

    assert response.status_code == 200
    assert response.get_json() == {"service": SERVICE_NAME, "version": VERSION}


def test_project_registry_lists_pulse_profile() -> None:
    response = create_app().test_client().get("/v1/projects")

    assert response.status_code == 200
    assert response.get_json() == {"projects": ["pulse-of-earth"], "count": 1}
