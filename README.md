# Dev-Copilot

> Autonomous AI Operations Consultant for engineering teams

An intelligent agent that connects to your GitHub, Jira, and Slack to analyze workflows, detect bottlenecks, and auto-generate optimized SOPs. Built with Claude for reasoning, Parallel for orchestration, and RedisVL for intelligent caching.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/DunngenMaster/dev-copilot.git
cd dev-copilot

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Configure your API keys for GitHub, Jira, Slack, etc.

# Run the backend
cd backend
uvicorn app.main:app --reload

# Run the frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## 🎯 What It Does

Dev-Copilot automatically:
- **Analyzes** your team's PR review times, bug assignment rates, and Slack blockers
- **Detects** workflow bottlenecks using measurable thresholds
- **Generates** optimized SOPs with SLAs and RACI matrices
- **Publishes** versioned reports to your knowledge base
- **Caches** insights to avoid expensive re-analysis

## 🏗️ Architecture

```
Frontend (Next.js) → Backend (FastAPI) → Parallel Agent → [GitHub/Jira/Slack APIs]
                                                      ↓
RedisVL (Cache/RAG) ← Sanity (Reports) ← Claude (SOP Generation)
```

## 📊 Key Metrics

**Pull Requests (14-day window)**
- Average time to first review
- Average time to merge
- Percentage of PRs waiting >36h for review
- Average reviews per PR

**Issues (Jira)**
- 24-hour unassigned rate
- Issue reopen rate
- 7-day stale issue ratio

**Slack Communication**
- Blocker mention frequency
- Top discussion terms
- Sample conversation links

## 🎯 Workflow Health Score

```python
score = 100 
  - (avg_review_time/24) * 10    # Review delays
  - unassigned_rate * 30         # Assignment gaps  
  - reopen_rate * 25             # Quality issues
  - stale_ratio * 20             # Process drift
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Reasoning** | Anthropic Claude | SOP generation & analysis |
| **Orchestration** | Parallel | Multi-step agent workflows |
| **Memory** | RedisVL | Vector embeddings & semantic cache |
| **APIs** | Postman Collections | GitHub/Jira/Slack integrations |
| **Security** | Skyflow | Tokenized identity management |
| **Knowledge Base** | Sanity | Versioned reports & SOPs |
| **Infrastructure** | AWS | Backend hosting & Redis cache |

## 📁 Project Structure

```
dev-copilot/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── agents/         # Parallel agent definitions
│   │   ├── core/           # Configuration & utilities
│   │   └── integrations/   # External API clients
│   ├── tests/              # Test suite
│   └── configs/            # Environment configs
├── frontend/               # Next.js application
│   ├── components/         # React components
│   ├── pages/              # Route handlers
│   └── hooks/              # Custom React hooks
├── postman/                # API collection definitions
├── redis/                  # Vector embeddings & cache
├── sanity/                 # CMS schemas & studio
├── docs/                   # Architecture & design docs
├── scripts/                # Deployment & data scripts
└── infra/                  # AWS, Docker, Parallel configs
```

## 🔧 Configuration

Create `.env` file with required API keys:

```env
# Core APIs
GITHUB_TOKEN=ghp_xxx
JIRA_URL=https://yourcompany.atlassian.net
JIRA_TOKEN=xxx
SLACK_BOT_TOKEN=xoxb-xxx

# AI Services
ANTHROPIC_API_KEY=sk-ant-xxx
PARALLEL_API_KEY=xxx

# Data Stores
REDIS_URL=rediss://default:password@your-redis-cloud-host:port
SANITY_PROJECT_ID=xxx
SANITY_DATASET=production

# Security
SKYFLOW_VAULT_ID=xxx
SKYFLOW_VAULT_URL=https://xxx.vault.skyflowapis.com
```

## 🚦 API Usage

**Analyze Team Workflow**
```bash
curl -X POST http://your-api-host:8000/analyze-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "github_repo": "owner/repo",
    "jira_project": "PROJ",
    "slack_channel": "#engineering",
    "window_days": 14
  }'
```

**Response Example**
```json
{
  "health_score": 73,
  "bottlenecks": [
    "41% of PRs wait >36h for first review",
    "18% issue reopen rate exceeds 10% threshold"
  ],
  "sop_preview": "## Goals\n1. Reduce PR review time to <24h...",
  "report_url": "https://dev-copilot.sanity.studio/reports/abc123",
  "cache_status": "MISS"
}
```

## 🔒 Security & Privacy

- **Slack**: Stores only message counts and permalinks, no message content
- **Identity**: Skyflow tokenizes user emails/IDs for privacy
- **Logs**: Automatically redact sensitive tokens
- **Reports**: Contain only aggregated metrics, no raw PII

## 🧪 Development

**Run Tests**
```bash
cd backend
pytest tests/ -v --cov=app
```

**Start Development Environment**
```bash
# Backend with hot reload
cd backend && uvicorn app.main:app --reload

# Frontend with hot reload  
cd frontend && npm run dev

# Sanity Studio
cd sanity && npm run dev
```

## 📈 Deployment

**AWS Deployment**
```bash
# Build and deploy backend
cd infra/aws
terraform init
terraform apply

# Deploy frontend to Vercel/AWS
cd frontend
npm run build
```

**Docker Deployment**
```bash
# Build all services
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [docs/architecture/](docs/architecture/)
- **API Collections**: [Postman Workspace](postman/)
- **Live Demo**: [Coming Soon]
- **Sanity Studio**: [Configure in sanity/](sanity/)
