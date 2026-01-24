1) Product Scope and User Flows
Core user journeys

Research Gap Discovery (Broad)

User types: “Computer Vision, classifiers, robust fine-grained recognition under distribution shift”

System returns a structured report:

Current trends

Representative recent papers

Open problems and “gaps”

Ranked research directions with rationale

Citations and links for every major claim

Deep Dive (Narrow Theme)

User picks a direction: “Long-tail fine-grained classification with label noise”

System generates a deep-dive brief:

Key subproblems, baseline methods, datasets

Proposed hypotheses and ablations

Experimental design and evaluation plan

Risks, common pitfalls, expected timelines

“Minimum publishable experiment set”

Paper Drafting

User uploads experiment outputs (CSV metrics, tables, notes, plots)

System produces a paper draft (IMRaD + references), then supports iterative edits in-app

Export to .docx so the user can finalize formatting and polishing

2) Recommended Tech Stack
Frontend (React)

React + TypeScript + Vite

UI: Tailwind + shadcn/ui (fast, clean components)

Chat UX: streaming responses, agent-step timeline, report viewer

Data fetching: TanStack Query

Real-time: SSE (EventSource) for streaming agent progress and partial outputs (simple and reliable)

Backend (Python)

FastAPI (async), Pydantic models

Agent orchestration: LangGraph (best for explicit multi-step workflows) or LangChain agents

LLM: Gemini via:

LangChain ChatGoogleGenerativeAI (langchain-google-genai)

Or the official Google Gen AI SDK (google-genai) if you prefer direct calls

Streaming: FastAPI StreamingResponse (SSE)

Search and Paper Metadata (the “internet” part)

For a hackathon, focus on high-signal academic sources first:

Semantic Scholar API for paper search, citations, venues, etc.

arXiv API for recent preprints and metadata
Optional:

Gemini “tools” capabilities (Google Search/URL context) if you choose that route later

Database and Storage

You do want persistence because “project” and “paper drafts” are key:

Postgres (recommended) with SQLAlchemy + Alembic

Easiest hosted: Neon/Supabase/Render Postgres

Hackathon fallback: SQLite locally, then switch to Postgres later

File storage:

Hackathon: local disk

Later: S3 / GCS / Supabase Storage

Word Export

python-docx to generate and update .docx

3) High-Level Architecture

React (client)

Auth (Google)

Chat (messages + streaming)

Project workspace (reports, deep dives, drafts)

Upload experiments

Inline editor for paper draft + export button

FastAPI (API)

Auth token verification and session/JWT

Project and conversation persistence

Agent-run orchestration + streaming logs

External retrieval (Semantic Scholar, arXiv)

Artifact generation (reports, plans, paper draft)

Docx export endpoint

Optional Worker (nice-to-have)

For long runs: Celery + Redis, or a lightweight background task queue

For hackathon: run agent jobs in-process, store run state in DB

4) Agent System Design (What makes it “agentic”)
Key principle

Agents must produce traceable intermediate artifacts (not just a final answer):

search queries used

papers found and filtered

extracted themes

explicit “gap hypotheses”

experiment plan

Agent roles (minimum set)

Scope Clarifier Agent

Takes user prompt and generates:

domain boundaries (CV → classification → subtopic)

constraints (datasets, compute, target venue)

query plan (keywords, synonyms)

Literature Scout Agent

Uses tools:

Semantic Scholar search (bulk/relevance search)

arXiv query

Outputs: candidate papers list with metadata, year, venue, citations, url, abstract

Trend Synthesizer Agent

Clusters papers into themes (methods, datasets, evaluation, constraints)

Outputs: “what’s hot now” and what’s saturating

Gap Miner Agent

Extracts “limitations” and “future work” cues from abstracts/snippets

Proposes gaps:

under-explored settings

evaluation blind spots

robustness and generalization failures

data and label constraints

Outputs ranked gaps with evidence references

Research Direction Generator

Converts gaps into 5 to 10 specific research directions

Each direction includes:

novelty angle

feasibility score

expected contribution type (method, benchmark, analysis)

minimum experiment set

Deep Dive pipeline (triggered after user selects a direction)

Deep Dive Scout

Runs targeted retrieval for that direction (new queries)

Focus: baselines, datasets, established metrics, known failure cases

Experiment Designer

Outputs:

hypotheses

baselines and ablations

dataset selection and preprocessing

training protocol guidance

evaluation plan and statistical testing suggestions

compute estimate + timeline

Paper pipeline (triggered after user uploads experiment results)

Paper Writer

Generates:

Outline first, then section drafts

Tables and figure callouts from user data

Strict rule: never invent numbers, always pull from uploaded results

Paper Editor Agent

Iterative revisions: clarity, structure, writing quality

Can apply user instructions: “make it more IEEE style”, “reduce length”, etc.

Tooling and orchestration

Prefer LangGraph so you can model:

state machine (Discovery → Deep Dive → Paper)

retries when retrieval is weak

human-in-the-loop checkpoints (user selects direction)

5) Retrieval and Citation Strategy (Critical for trust)
Data sources to start (fast and high-signal)

Semantic Scholar and arXiv metadata/abstracts are enough for a strong hackathon demo

Save per-paper:

title, authors, year, venue

abstract

url

citation count (when available)

Evidence discipline

Every report section should include a “Key sources” list

Store citations in DB as structured objects:

source_id, url, title, year, snippet_used, accessed_at

This prevents “hand-wavy” claims and makes your output look research-grade.

6) Authentication (Google Sign-In)
Recommended hackathon approach

Frontend: Google Identity or Firebase Auth with Google provider

Backend: verify Google ID token server-side using Google’s recommended verification flow in Python

Backend session strategy

After token verification:

create or fetch user record

issue your own JWT or HttpOnly session cookie

Store user id, email, name, avatar in DB

7) Database Schema (Practical MVP)

Users

id, email, name, avatar_url, created_at

Projects

id, user_id, title, domain_tags, created_at

Conversations

id, project_id

Messages

id, conversation_id, role (user/assistant/agent), content, created_at

AgentRuns

id, project_id, run_type (discovery/deep_dive/paper), status, started_at, finished_at

RunEvents (for streaming logs)

id, run_id, event_type (tool_call, tool_result, agent_note, partial_output), payload_json, created_at

Artifacts

id, project_id, artifact_type (trend_report, deep_dive_report, paper_draft), content_markdown, version, created_at

Sources

id, project_id, provider (s2/arxiv/url), title, authors, year, url, abstract, meta_json

ExperimentUploads

id, project_id, file_path, file_type, meta_json, created_at

8) API Design (FastAPI)
Auth

POST /auth/google (send ID token, verify, return session/JWT)

Projects

POST /projects

GET /projects

GET /projects/{id}

Chat + runs

POST /projects/{id}/message (adds user message, optionally starts run)

POST /projects/{id}/runs/discovery

POST /projects/{id}/runs/deep-dive (with chosen direction id)

POST /projects/{id}/runs/paper (after experiment upload)

Streaming

GET /runs/{run_id}/events (SSE stream of RunEvents)

Artifacts

GET /projects/{id}/artifacts

PUT /artifacts/{artifact_id} (store edited draft)

Uploads

POST /projects/{id}/experiments/upload (CSV/JSON/images)

GET /projects/{id}/experiments

Export

POST /artifacts/{artifact_id}/export/docx (returns a .docx)

9) Frontend Implementation Plan (React)
Screens

Login page

Project dashboard

Project workspace

Left: project sidebar (Artifacts, Sources, Experiments)

Center: Chat

Right: “Agent Timeline” + “Run Status”

Artifact editor

Markdown preview + editable sections

“Ask agent to revise” box

Experiment upload + mapping

Upload files, label what each file contains (metrics table, confusion matrix, etc.)

Streaming UX (big demo value)

While run executes:

show agent step cards in timeline:

“Searching Semantic Scholar…”

“Found 50 papers, filtering…”

“Extracting themes…”

show partial report sections as they complete

10) Paper Draft Generation (How it actually works)
Inputs

Selected direction + deep-dive report

Experiment files:

metrics CSV

ablation tables

notes (free text)

optionally figures (png)

Output structure (stored as editable Markdown + exported to DOCX)

Title

Abstract

Introduction (problem, motivation, contributions)

Related Work (grouped themes + citations)

Method (your proposed approach)

Experiments (setup, datasets, baselines)

Results (tables and narrative)

Discussion/Limitations

Conclusion

References

Export logic

Convert Markdown sections to docx paragraphs with python-docx

Add references list at end

Optionally use a template .docx to preserve formatting (conference-like style)