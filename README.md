# dev-copilot

## 1) Summary

Autonomous AI Operations Consultant for engineering teams. It connects to GitHub, Jira, and Slack; analyzes bug-fixing workflows; detects bottlenecks; and auto-generates a versioned SOP. Uses Claude for reasoning, Parallel for agent orchestration, RedisVL for memory/RAG + semantic cache, Postman for API workflows, Skyflow for secure identity tokens, Sanity as the knowledge base, and AWS for hosting.

## 2) Problem

Teams suffer from slow PR reviews, unassigned/reopened bugs, repeated Slack questions, and stale SOPs—no unified operational intelligence or memory.

## 3) Solution

A production-style agent that:

- Collects workflow signals (PRs, issues, Slack blockers)
- Detects bottlenecks and computes a deterministic score
- Retrieves prior SOPs via RAG
- Generates an optimized SOP + RACI
- Publishes a versioned report to Sanity and caches memory in RedisVL

## 4) Core Features

- Automated workflow diagnostics (PR timings, unassigned rate, reopen rate, stale bugs)
- Bottleneck statements with thresholds (e.g., "41% PRs wait >36h for first review")
- RAG-powered SOP generation (<700 words) with SLAs and RACI
- Semantic caching to skip expensive reanalysis on similar contexts
- Versioned reports with history and a public Sanity page

## 5) Tech Stack (sponsor alignment)

- **Anthropic (Claude)** – reasoning & SOP generation
- **Parallel** – multi-step agent plan & tool calls
- **RedisVL** – vector store for RAG + semantic cache
- **Postman** – GitHub/Jira/Slack API collections
- **Skyflow** – tokenized identity mapping (emails ↔ Slack/GitHub IDs)
- **Sanity** – versioned knowledge base & report viewer
- **AWS** – hosting (backend/container), optional ElastiCache for Redis

## 6) Architecture (high-level)

- **Frontend (Next.js)**: Inputs (repo/team), result card (Score, Bottlenecks, SOP preview), link to Sanity report.
- **Backend (FastAPI)**: /analyze-workflow orchestrates: cache → fetch → summarize → RAG → reason → persist.
- **Parallel Agent**: executes plan: Redis check → Postman calls → summarize → RAG → Claude → Sanity → Redis upsert.
- **Data Stores**: RedisVL (embeddings, cached analyses), Sanity (versioned reports), Skyflow (tokens only).

## 7) Data Flow (condensed)

```
User → Frontend → Backend → RedisVL (cache HIT?)
MISS → Parallel → Postman(GitHub/Jira/Slack) → summarize METRICS → RedisVL (RAG) → Claude (bottlenecks+SOP) → score() → Sanity save → Redis upsert → Backend → Frontend.
```

## 8) Metrics (14-day default window)

- **PRs**: avg_time_to_first_review_h, avg_time_to_merge_h, %PRs >36h w/o first review, avg_reviews_per_pr
- **Issues (Jira)**: unassigned_24h_rate, reopen_rate, stale_7d_ratio
- **Slack**: blocker_mentions, top_terms, sample_permalinks (no long-term message bodies)

## 9) Score (deterministic)

```python
score = 100
  - w1*clamp(avg_time_to_first_review/24,0,3)*10
  - w2*unassigned_24h_rate*30
  - w3*reopen_rate*25
  - w4*stale_7d_ratio*20
```

Default weights: w1=1.0, w2=1.0, w3=1.0, w4=0.8 (stored/editable in Sanity).

## 10) Outputs

- Workflow Health Score (0–100)
- Bottlenecks (3–5 measurable statements)
- Optimized SOP (Goals, SLAs, Auto-triage, Assignment, PR Review, QA Gates, Weekly cadence, RACI)
- Versioned report in Sanity (public URL)
- Cache status (HIT/MISS) for transparency

## 11) Security & Privacy

- **Slack**: store only counts + permalinks, no long-term message text
- **Skyflow**: tokenized identities; backend resolves display names just-in-time
- **Logs**: redact tokens; Sanity stores summaries, not raw PII

## 12) Repository Structure

```
dev-copilot/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── utils/
│   │   ├── core/
│   │   └── integrations/
│   │       ├── github/
│   │       ├── jira/
│   │       ├── slack/
│   │       ├── redis/
│   │       ├── sanity/
│   │       ├── skyflow/
│   │       └── postman/
│   ├── tests/
│   ├── configs/
│   └── logs/
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   ├── styles/
│   ├── utils/
│   └── public/
├── postman/
│   ├── collections/
│   └── environments/
├── redis/
│   ├── embeddings/
│   └── cache/
├── sanity/
│   ├── schemas/
│   └── studio/
├── docs/
│   ├── architecture/
│   ├── design/
│   └── demo-assets/
├── scripts/
│   ├── deploy/
│   └── data/
├── infra/
│   ├── aws/
│   ├── docker/
│   └── parallel/
└── requirements.txt
```
