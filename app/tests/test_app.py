"""Tests for the AAP Demo Flask application."""

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_contains_title(client):
    response = client.get("/")
    assert b"Welcome to AAP Demo" in response.data


def test_index_contains_version(client):
    response = client.get("/")
    assert b"VERSION 1.0.0" in response.data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


def test_health_returns_json(client):
    response = client.get("/health")
    assert response.content_type == "application/json"
