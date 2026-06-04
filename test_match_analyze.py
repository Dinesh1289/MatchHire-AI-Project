"""
Integration tests for POST /api/v1/matches/analyze.

Uses FastAPI TestClient with a real ParsedResume payload
(as returned by /resumes/upload) to verify the full pipeline.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# Minimal ParsedResume payload — mirrors the schema exactly
SAMPLE_PARSED_RESUME = {
    "contact": {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "+1 555 123 4567",
    },
    "summary": "Senior backend engineer with 6 years building scalable systems.",
    "skills": [
        {"name": "python", "category": "language"},
        {"name": "fastapi", "category": "technical"},
        {"name": "postgresql", "category": "technical"},
        {"name": "docker", "category": "technical"},
        {"name": "redis", "category": "technical"},
        {"name": "kubernetes", "category": "technical"},
        {"name": "aws", "category": "technical"},
    ],
    "work_experience": [
        {
            "company": "Acme Corp",
            "title": "Senior Backend Engineer",
            "bullets": ["Led migration to microservices", "Reduced latency by 40%"],
            "technologies": ["python", "fastapi", "postgresql", "docker"],
        }
    ],
    "education": [
        {
            "institution": "MIT",
            "degree": "Bachelor's in Computer Science",
            "field_of_study": "Computer Science",
        }
    ],
    "projects": [],
    "achievements": [],
    "certifications": [],
    "ats_keywords": ["python", "fastapi", "postgresql", "docker", "redis", "kubernetes", "aws"],
    "total_years_experience": 6.0,
    "seniority_level": "senior",
    "raw_text_length": 1200,
    "parser_version": "1.0.0",
    "confidence_score": 0.87,
}

SAMPLE_JD_TEXT = """
Senior Backend Engineer

Requirements
- 5+ years of Python experience
- Strong experience with FastAPI or Django
- PostgreSQL and Redis
- Docker and Kubernetes
- AWS experience

Preferred
- Kafka or RabbitMQ
- Terraform

Responsibilities
- Build scalable REST APIs
- Participate in architecture reviews
- Mentor engineers

Education
Bachelor's degree in Computer Science or related field
"""


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestMatchAnalyzeEndpoint:

    def test_returns_200_for_valid_request(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={
                "parsed_resume": SAMPLE_PARSED_RESUME,
                "jd_text": SAMPLE_JD_TEXT,
                "job_title_hint": "Senior Backend Engineer",
            },
        )
        assert response.status_code == 200

    def test_response_has_result_shape(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={
                "parsed_resume": SAMPLE_PARSED_RESUME,
                "jd_text": SAMPLE_JD_TEXT,
            },
        )
        body = response.json()
        assert "result" in body
        result = body["result"]
        assert "match_score" in result
        assert "match_score_pct" in result
        assert "match_tier" in result
        assert "breakdown" in result
        assert "matched_skills" in result
        assert "missing_skills" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "recommendation" in result
        assert "parsed_jd" in result

    def test_match_score_in_valid_range(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={
                "parsed_resume": SAMPLE_PARSED_RESUME,
                "jd_text": SAMPLE_JD_TEXT,
            },
        )
        result = response.json()["result"]
        assert 0.0 <= result["match_score"] <= 1.0
        assert 0.0 <= result["match_score_pct"] <= 100.0

    def test_strong_candidate_scores_high(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={
                "parsed_resume": SAMPLE_PARSED_RESUME,
                "jd_text": SAMPLE_JD_TEXT,
                "job_title_hint": "Senior Backend Engineer",
            },
        )
        result = response.json()["result"]
        # This candidate has nearly all required skills
        assert result["match_score"] >= 0.55

    def test_breakdown_weights_sum_to_one(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={
                "parsed_resume": SAMPLE_PARSED_RESUME,
                "jd_text": SAMPLE_JD_TEXT,
            },
        )
        breakdown = response.json()["result"]["breakdown"]
        dimensions = [
            "skills_match", "experience_match", "title_similarity",
            "keyword_match", "education_match"
        ]
        total_weight = sum(breakdown[dim]["weight"] for dim in dimensions)
        assert abs(total_weight - 1.0) < 0.001

    def test_recommendation_has_required_fields(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={
                "parsed_resume": SAMPLE_PARSED_RESUME,
                "jd_text": SAMPLE_JD_TEXT,
            },
        )
        rec = response.json()["result"]["recommendation"]
        assert "action" in rec
        assert "headline" in rec
        assert "rationale" in rec
        assert "next_steps" in rec
        assert len(rec["next_steps"]) >= 1

    def test_returns_422_for_short_jd(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={
                "parsed_resume": SAMPLE_PARSED_RESUME,
                "jd_text": "Too short",
            },
        )
        assert response.status_code == 422

    def test_returns_422_for_missing_resume(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={"jd_text": SAMPLE_JD_TEXT},
        )
        assert response.status_code == 422

    def test_501_when_resume_id_provided(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={
                "resume_id": "00000000-0000-0000-0000-000000000001",
                "jd_text": SAMPLE_JD_TEXT,
            },
        )
        assert response.status_code == 501

    def test_company_name_and_title_hint_accepted(self, client):
        response = client.post(
            "/api/v1/matches/analyze",
            json={
                "parsed_resume": SAMPLE_PARSED_RESUME,
                "jd_text": SAMPLE_JD_TEXT,
                "job_title_hint": "Backend Lead",
                "company_name": "Stripe",
            },
        )
        assert response.status_code == 200
        # Title hint should be used in parsed_jd
        result = response.json()["result"]
        assert result["parsed_jd"]["title"] == "Backend Lead"
        assert result["parsed_jd"]["company"] == "Stripe"
