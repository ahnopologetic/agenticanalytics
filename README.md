# Agentic Analytics

Agentic Analytics is a rapid, code-integrated tracking plan automation tool for fast-moving startup teams. With a GitHub-first setup, it instantly turns codebase changes into actionable, shared analytics plans—bridging engineers, planners, and stakeholders with clear automated contracts.

## Features

- **GitHub Integration:** Connect your GitHub account, select repos, and auto-generate a tracking plan from your codebase.
- **Automated Tracking Plan:** Keeps your analytics tracking plan up to date as your code evolves.
- **Role-Based Views:** Tailored dashboards for Engineers, PMs, and Decision Makers.
- **PR Checks:** Automated validation and inline feedback for analytics event consistency in GitHub pull requests.
- **Minimal Setup:** Onboard and generate your first tracking plan in under 5 minutes.

## Getting Started

1. **Connect with GitHub:** Sign in with your GitHub account and select repositories to analyze.
2. **Auto-Generate Plan:** The backend scans your codebase and creates an initial tracking plan.
3. **Review & Maintain:** View, edit, and export your tracking plan. Get feedback directly in GitHub PRs.

## Tech Stack

- **Backend:** FastAPI, Supabase, GitHub API
- **Frontend:** (Planned) React/Next.js, TailwindCSS

## MVP Limitations

- Only GitHub integration (no other VCS).
- Focused on JavaScript/TypeScript codebases for event extraction.
- Not a full analytics dashboard—focus is on tracking plan automation.

## License

MIT

---

For more details, see [docs/prd.md](docs/prd.md).