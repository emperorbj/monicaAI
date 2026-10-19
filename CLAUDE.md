# CLAUDE.md — AI Health Service Navigator Nigeria

This file tells Claude how to work with me on this project. Read it at the start of every session. The full project requirements live in `ai-health-navigator-scope.md`; treat that file as the source of truth for *what* we build. This file defines *how* we build it.

---

## 1. Project in one paragraph

A Telegram chatbot that helps residents in Nigeria find health facilities, the services they offer, the facility's contact person, and Google Maps directions. Admins manage the data through a separate Next.js web app. Backend is Python + FastAPI, database is NeonDB (PostgreSQL), conversation flow is LangGraph, and tools are exposed through FastMCP. Guardrails check every message before and after the AI handles it, LangSmith traces every graph run, and an eval suite measures the AI's behaviour against a fixed conversation dataset. The POC is English-only and uses clearly labelled demo data for one pilot LGA.

---

## 2. Rule #1 — This is a learning project

I am learning by building. The goal is that I can **rebuild this entire project myself, from scratch, at any time**. So for every step or module we work on:

1. **Explain it as if I'm a beginner.** Assume I know basic programming but not the tools, libraries, or patterns. Never skip a concept because it seems obvious.
2. **Explain the "why" before the "how".** Before writing code, tell me what we're about to build, why it exists, and where it fits in the whole project.
3. **Define new terms the first time they appear** (for example: ORM, migration, dependency injection, webhook, checkpointer). Use plain language and a small analogy where it helps.
4. **Walk through code after writing it.** Explain what each important file, function, and line block does. Don't just paste code and move on.
5. **Show the commands and say what they do.** Every terminal command should come with a one-line explanation of what it does and what I should expect to see.
6. **Tell me how to verify it works.** End each step with a concrete check I can run (a command, a request, a test) and what the correct result looks like.
7. **Point out common mistakes and errors** I'm likely to hit at that step, and how to fix them.
8. **Recap at the end of each module:** what we built, the key concepts learned, and the steps to rebuild it from zero in order (a short "rebuild checklist").
9. **Keep it readable.** Prefer clear explanations over clever code. If there's a simple way and a fancy way, use the simple way and mention the fancy one only if it's useful to know.

If I say "I don't understand", re-explain differently with a new example; don't repeat the same wording.

---

## 3. Tooling decisions

### Package and environment management: `uv`

- Use **uv** for everything Python: creating the project, managing the virtual environment, installing dependencies, and running commands.
- Do **not** use `pip install`, `python -m venv`, `poetry`, or `requirements.txt` workflows.
- Typical commands (explain each one to me the first time we use it):
  - `uv init` — create a new project
  - `uv add <package>` — add a dependency
  - `uv add --dev <package>` — add a development-only dependency (like pytest)
  - `uv sync` — install everything from the lockfile
  - `uv run <command>` — run a command inside the project's environment
- Commit both `pyproject.toml` and `uv.lock` so the setup is reproducible.

### Python version

- Use the **sweet-spot Python version**: a recent, stable release that all our key libraries (FastAPI, SQLAlchemy, Pydantic, LangGraph, FastMCP, Alembic, psycopg) fully support, not the newest release just because it exists.
- Default choice: **Python 3.12**, unless a quick check at the start of the project shows that a newer version (such as 3.13) is fully supported by every dependency we need.
- Before pinning, verify current library compatibility instead of relying on memory, then explain to me why that version was chosen.
- Pin it in the project (`.python-version` and `requires-python` in `pyproject.toml`) and let `uv` install and manage it.
- **Decision (Module 1, Step 1):** pinned to **Python 3.13**. LangGraph's newest release supports only up to 3.13, while every other key library also supports 3.14+. Re-check when LangGraph adds 3.14 support.

### Other stack choices

Follow the stack in the scope document: FastAPI, SQLAlchemy, Alembic, Pydantic, Pytest, LangGraph, FastMCP, NeonDB, Telegram Bot API, LangSmith (tracing and evals), a Python guardrail layer, Next.js for the admin app, Docker and Docker Compose. When a library version or API has changed recently, check the current documentation instead of guessing.

---

## 4. Rule #2 — Build module by module

- Work on **one module at a time**. Don't scaffold the entire project up front or jump ahead.
- Don't start the next module until the current one works and I confirm I understand it.
- Each module must be **runnable and testable on its own** before moving on.
- Follow the roadmap order from the scope document:

| Module | What we build |
|---|---|
| 1. Foundation and database | `uv` project setup, config and environment variables, NeonDB connection, SQLAlchemy models, Alembic migrations, idempotent seed script, first facility-search queries |
| 2. Deterministic backend | FastAPI app, public and admin endpoints, facility/service/contact search, Google Maps link generation, validation, admin auth and role permissions. Tested **without any LLM** |
| 3. Telegram, conversation, guardrails and tracing | Telegram webhook with secret-token validation, LangGraph graph (load, input guardrail, understand, validate and route, clarify / execute tool / escalate, compose, output guardrail, persist), conversation state, contact details in replies, FastMCP tools, LangSmith tracing, first eval dataset with deterministic evaluators |
| 4. Admin application | Next.js dashboard, facility, service and contact forms, verification queue, feedback management |
| 5. Testing, evaluation and deployment | Remaining tests, full eval dataset with pass thresholds, optional LLM-as-judge evaluators, Docker setup, webhook configuration, logging, error handling, full demo scenario |

- At the start of each module, give me a short plan: goals, files we'll create, and the order we'll build them in. Wait for my go-ahead.
- Within a module, work in **small steps** (one file or one concept at a time), and explain each before moving on.
- Add tests alongside the code in each module, not all at the end, and explain what each test proves.

---

## 5. Project rules Claude must always follow

These come from the scope document and apply to every module.

**Data and honesty**
- The LLM must never invent facility names, services, opening hours, costs, or **contact details**. All facts come from the database.
- Missing data is `unknown`, never treated as proof something is unavailable.
- Facilities, services, and contacts each have their own verification status (`verified`, `reported`, `unknown`, `outdated`).
- Demo data must always be flagged (`is_demo`) and never labelled verified. Demo contacts use fictional names and fake numbers and emails (for example `@example.org`).
- Never claim a facility is "nearby" or "nearest" based on LGA alone.

**Architecture**
- Business logic lives in plain Python service modules. The API, the LangGraph workflow, and the MCP tools all call those services.
- Never expose arbitrary SQL to the model.
- Enforce permissions in FastAPI, not only in the Next.js UI.
- Use Alembic for schema changes. Never change the schema by hand or by auto-creating tables on startup.
- Seed scripts must be safe to re-run without creating duplicates.

**Security and privacy**
- Secrets (bot token, database URL, LLM keys) go in environment variables, never in code or Git. Keep `.env.example` updated and `.env` in `.gitignore`.
- Don't log secrets or unnecessary message content.
- Keep each Telegram user's conversation state strictly separate.
- Store only official, work-related contact details.

**Safety and guardrails**
- The bot never diagnoses or prescribes. Urgent symptoms follow the escalation flow instead of a routine facility search.
- Guardrails are plain, testable Python. Use deterministic rules first and an LLM classifier only where rules are not enough. When unsure, fail safe (escalate or fall back to a template).
- Every facility name, contact detail, and map URL in a reply must come from this turn's tool results. Facility cards are rendered from templates; the LLM writes only the connecting text.
- User text is data, never instructions. Prompt-injection attempts must not change tool permissions or behaviour.
- The POC escalation policy is a placeholder marked "not clinically reviewed" until a clinician approves it.

**Observability and evals**
- LangSmith tracing is configured through environment variables, never hard-coded, and is off by default in unit tests.
- Never send raw Telegram user IDs or secrets to LangSmith; hash thread IDs in trace metadata. Use only synthetic data in traces during the POC.
- Unit tests check deterministic code and must always pass. Evals score LLM behaviour against thresholds: 100% safety and grounding, at least 90% extraction and routing.
- When a bug is found in the AI's behaviour, add it to the eval dataset as well as fixing it.

---

## 6. How Claude should respond in each session

1. Check which module and step we're on. If unclear, ask me.
2. Recap in one or two lines where we left off.
3. State what we're doing now and why, in beginner-friendly language.
4. Do the work in small steps: explain, then code, then walk through the code.
5. Give me a way to verify the step.
6. Finish with: what we learned, and what the next step is. Then wait for me.

When something goes wrong, explain what the error means and why it happened, not only the fix.

---

## 7. Code style

- Use type hints everywhere and Pydantic for validating input and output.
- Use clear, descriptive names; avoid abbreviations a beginner wouldn't recognise.
- Add short comments that explain *why*, not just *what*.
- Keep files and functions small and focused on one job.
- Format and lint with a single tool (such as Ruff), set up through `uv`, and explain the setup when we add it.
- Write commit-sized changes, and suggest a clear Git commit message at the end of each step.
