# AI-Powered Resume ↔ Job Matching Engine

An intelligent backend system that analyzes resumes against job descriptions and generates explainable match scores, skill gap analysis, recommendations, and ATS insights.

Built as a product-focused AI system combining:
- NLP-based parsing
- Skill extraction
- Resume-job semantic matching
- Explainable scoring architecture
- Product thinking + backend engineering

---

# Problem Statement

Most job portals provide poor-quality resume matching with little transparency.

Candidates often:
- Don't know why they were rejected
- Lack guidance on missing skills
- Cannot understand ATS optimization
- Receive generic match scores

This project solves that by building an explainable AI-powered matching engine that:
- Parses resumes and JDs
- Extracts structured data
- Calculates weighted fit scores
- Identifies missing skills
- Generates actionable recommendations

---

# Features

## Resume Parsing
- Contact extraction
- Skills extraction
- Experience parsing
- Education parsing
- ATS keyword generation

## Job Description Parsing
- Required skills extraction
- Preferred skills extraction
- Seniority detection
- Experience requirement extraction
- Degree requirement extraction

## Matching Engine
Weighted multi-dimensional scoring:

| Dimension | Weight |
|---|---|
| Skills Match | 40% |
| Experience Match | 30% |
| Title Similarity | 15% |
| Keyword Match | 10% |
| Education Match | 5% |

---

# Explainable AI Matching

The system generates:
- Match score
- Match tier
- Strengths
- Weaknesses
- Missing skills
- Bonus skills
- Recommendations
- Skill gap analysis

---

# Tech Stack

## Backend
- Python
- FastAPI
- Pydantic

## NLP & Processing
- Regex-based NLP pipeline
- Skill normalization engine
- Deterministic parsing architecture

## Development
- GitHub
- Postman
- Uvicorn

---

# Architecture

```text
Resume Input
      ↓
Resume Parser
      ↓
Structured Resume Data
      ↓
Matching Engine
      ↓
JD Parser
      ↓
Weighted Scoring
      ↓
Recommendations + Skill Gap Analysis
```

---

# Current Progress

## Completed
- Resume parser
- JD parser
- Skill normalization
- Matching engine
- Weighted scoring system
- ATS keyword extraction

## In Progress
- Semantic similarity improvements
- Embedding-based matching
- Frontend dashboard
- Resume upload UI
- Analytics layer

---

# Sample Use Case

Input:
- Candidate resume
- Product Manager JD

Output:
- Match Score: 78%
- Skill Gap Analysis
- ATS Keyword Match
- Personalized Recommendation

---

# Product Thinking Behind the System

This project was designed not just as an engineering system, but as a product-focused AI workflow.

Key PM considerations:
- Explainability over black-box AI
- Actionable recommendations
- Recruiter + candidate usability
- Scalable scoring architecture
- Extensible matching dimensions

---

# Future Improvements

- LLM-powered semantic matching
- Vector embeddings
- Recruiter dashboard
- Resume optimization assistant
- Interview readiness scoring
- Job recommendation engine

---

# Repository Structure

```text
app/
 ├── api/
 ├── services/
 ├── schemas/
 ├── utils/
 ├── core/
```

---

# Author

Dinesh C
LinkedIn:(https://www.linkedin.com/in/dinesh-chandru/)
