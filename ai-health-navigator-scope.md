# AI Health Service Navigator — Full Project Scope

## 1. Project overview

**Project name:** AI Health Service Navigator Nigeria

**Project type:** Conversational AI application for public health service discovery.

**Primary goal:** Help people in Nigeria discover health facilities, find the services they provide, understand how to access those services, get directions to the facilities, and know who to contact at each facility.

The application allows residents to chat naturally with a Telegram bot instead of navigating complicated government websites or calling multiple health facilities to find the service they need.

For the proof of concept (POC), residents interact through Telegram, while administrators use a separate web application to manage facilities, services, locations, contact persons, and verification records.

The initial release supports English only. It uses a seeded database containing demonstration data, making it possible to demonstrate the complete workflow before obtaining and verifying a real-world health facility dataset.

### The problem we are solving

A resident might need antenatal care, childhood vaccination, malaria testing, family planning, or another primary healthcare service but may not know:

- Which nearby public health facilities provide that service.
- Which facility to contact or visit.
- **Who to contact at the facility, and how to reach them.**
- Where the facility is located.
- How to get directions through Google Maps.
- Whether information about the facility, service, or contact person has actually been verified.

The navigator reduces the effort needed to find this information and makes it easier to take the next step.

---

## 2. Project objectives

1. Allow residents to describe their healthcare navigation needs in ordinary English.
2. Find relevant facilities using structured, reliable database records.
3. Ask only for essential information that is missing from a request.
4. Remember relevant details across multiple Telegram messages.
5. Filter facilities by state, Local Government Area (LGA), service, and other supported criteria.
6. Provide latitude, longitude, and clickable Google Maps directions links where verified coordinates exist.
7. **Provide the facility's contact person details (name, role, phone, and email where available) in every facility result.**
8. Clearly distinguish verified, reported, unknown, and outdated information.
9. Give administrators a secure interface for managing facilities, services, and contact persons.
10. Demonstrate a complete end-to-end workflow using seeded sample data.
11. Keep the system modular so that the bot, admin app, and AI workflow share the same business logic.
12. **Protect residents with guardrails** that check messages before and after the AI handles them, so the bot stays in scope, escalates urgent cases, and never sends ungrounded facts.
13. **Make the AI workflow observable with LangSmith tracing**, so every conversation turn, LLM call, and tool call can be inspected and debugged.
14. **Measure AI quality with evaluations (evals)** on a fixed dataset of realistic conversations, so prompt, model, or graph changes can be compared before release.

---

## 3. Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Resident interface | Telegram Bot API | Natural-language chat, follow-up questions, facility results, contact details, and clickable map links. |
| Admin interface | Next.js | Separate web application for facility, service, location, schedule, contact person, and verification management. |
| Backend | Python and FastAPI | REST endpoints, Telegram webhook, authentication, business rules, and database access. |
| Conversation orchestration | LangGraph | Intent extraction, clarification, tool routing, conversation state, and multi-turn continuity. |
| Database | NeonDB | Managed PostgreSQL for facilities, LGAs, services, contacts, verification history, user preferences, and conversation state. |
| Tool integration | MCP / FastMCP | Expose controlled health-navigation tools to the AI workflow when needed. Core business logic stays in ordinary Python services. |
| Navigation | Google Maps URLs | Generate map and directions links from stored facility coordinates; no Maps API key is required just to construct these links. |
| Guardrails | Python guardrail layer (Pydantic + deterministic rules, with an LLM classifier where rules are not enough) | Check resident input (urgent symptoms, out-of-scope requests, prompt injection, sensitive data) and model output (grounding, safety wording, status labels) before anything reaches the user. |
| Observability | LangSmith | Trace each LangGraph run: nodes, LLM calls, tool calls, latency, token usage, and errors. |
| Evaluation | LangSmith datasets and experiments, run from a Python eval script | Score the AI workflow against a versioned dataset of realistic conversations and compare results across changes. |

**Supporting tools:** SQLAlchemy, Alembic, Pydantic, Pytest, Git, Docker, and Docker Compose. Use a suitable LLM provider or a local model for conversational understanding, keeping costs and usage limits in mind.

**Database decision:** NeonDB is the source of truth. The application uses PostgreSQL-compatible queries and migrations.

---

## 4. Scope of the MVP

The first version is small enough to build, but complete enough to demonstrate a serious AI engineering project.

### Included in the MVP

- English-language Telegram assistant.
- Natural conversation and multi-turn context.
- State and LGA selection or extraction from messages.
- Facility and service discovery from NeonDB.
- Facility details and Google Maps directions links.
- **Facility contact person details included in facility responses.**
- Admin login and role-based permissions.
- Seeded demonstration facilities, services, and contact persons.
- Verification status and source tracking (for facilities, services, and contacts).
- Automated tests and Docker-based local deployment.
- Input and output guardrails around the conversation workflow.
- LangSmith tracing for the LangGraph workflow.
- An evaluation dataset and eval suite with pass thresholds for the AI behaviour.

For the demonstration, seed a small, clearly labelled dataset for one pilot LGA. The dataset can be expanded later without redesigning the application.

---

## 5. Resident user experience

The Telegram bot should feel like a helpful person assisting the user, not a rigid form.

### Example first-time conversation

> **User:** Hi, I need a place for antenatal care.
>
> **HEALTH NAVIGATOR:** Hello! I can help you find facilities that offer antenatal care. Which state and LGA should I search in?
>
> **User:** Oyo State, Ibadan North.
>
> **HEALTH NAVIGATOR:** I'll look for antenatal care facilities in Ibadan North. Here are the matching facilities I found.

**HEALTH NAVIGATOR · FACILITY RESULT**

**Example Primary Health Centre**
Ibadan North, Oyo State

- **Service:** Antenatal care
- **Location:** 7.4123, 3.9056 (illustrative coordinates)
- **Contact person:** Jane Doe (Demo), Officer-in-Charge
- **Phone:** +234 000 000 0000 (demonstration number)
- **Email:** demo.contact@example.org (demonstration address)
- **Status:** Demonstration data — not verified
- [Get directions on Google Maps]

> **User:** Do they open on Saturdays?
>
> **HEALTH NAVIGATOR:** I'll check the available opening-hour information. I won't assume they're open on Saturdays unless we have reliable information confirming it.

*Illustrative interaction only. The example facility, coordinates, and contact person must not be represented as real or verified.*

### Conversation behaviour requirements

The bot must:

- Allow users to describe their needs before asking about their location.
- Extract multiple details from one message when possible.
- Ask one concise clarifying question when an essential detail is missing.
- Remember the requested service and area during follow-up questions.
- Understand references such as "the first one", "another facility", and "what about vaccination instead?"
- Keep the existing location when the user changes only the requested service.
- Support `/start`, `/help`, `/location`, and `/reset` commands.
- Allow users to change their saved state and LGA.
- Clearly indicate when no matching facility is found.
- Avoid claiming that a facility is nearby or nearest based on LGA alone.
- **Include the facility's contact person details in each facility result, and answer follow-ups such as "who do I call?" or "what's their number?" from stored contact records.**
- **State clearly when no contact person is on record for a facility, rather than guessing or inventing one.**

The user's saved LGA can make future searches easier, but it must not be treated as the user's precise current location.

---

## 6. Facility discovery, contacts, and Google Maps

### How the search works

The resident's message is converted into a structured request. For example:

```json
{
  "intent": "search_facilities",
  "service_code": "antenatal_care",
  "state_name": "Oyo",
  "lga_name": "Ibadan North"
}
```

The backend then:

1. Validates the requested service and resolves the state and LGA.
2. Queries NeonDB for matching facilities.
3. Retrieves their service records, contact persons, and verification status.
4. Orders the results using an explicit, explainable rule.
5. Formats the facility information, contact details, and map links.
6. Returns the results to the conversation workflow.

The LLM must not invent facility names, service availability, or contact details.

### Google Maps link formats

For opening the facility's location:

```
https://www.google.com/maps/search/?api=1&query=LATITUDE%2CLONGITUDE
```

For navigating to the facility:

```
https://www.google.com/maps/dir/?api=1&destination=LATITUDE%2CLONGITUDE
```

Replace the coordinate placeholders with actual stored values. The backend must generate the URLs using URL encoding rather than manually concatenating untrusted input.

### Each facility response includes, where available

- Facility name.
- Address and LGA.
- Services that match the request.
- Latitude and longitude.
- **Contact person: name, role/title, phone number, and email address.**
- **Verification status and last verification date for the contact details.**
- Verification status and last verification date for the facility and service.
- Google Maps location or directions link.
- Opening hours only when supported by reliable data.

### Contact person rules

- A facility may have one or more contact persons; one may be flagged as the **primary contact**, and the primary contact is shown first.
- If several contacts exist, the bot shows the primary contact and offers to share the others on request.
- Only official, work-related contact details (facility desk, officer-in-charge, service-unit lead) are stored and shared. Personal contact details of staff must not be stored or shown.
- Contact details are shown exactly as stored; the bot never infers, completes, or invents a name, phone number, or email.
- Contact details carry their own verification status, independent of the facility and service status. Unverified or outdated contacts are clearly labelled as such.
- Where a contact person is specific to a service (for example, the antenatal clinic lead), the service-specific contact is shown for that service; otherwise the facility's general contact is shown.
- Phone numbers are stored in international format (E.164) and validated before saving.

### Separate verification statuses

Coordinates, service information, and contact details each have separate verification statuses. A correct map pin does not prove that a facility provides a particular service, and a listed service does not prove that a contact person is current.

### Geographic search

For the MVP, filtering by state and LGA is sufficient. The bot does not collect GPS coordinates from residents.

---

## 7. Database design — NeonDB / PostgreSQL

Use a relational schema with clear foreign keys. The following is the proposed logical model; exact SQL types and constraints are finalised during implementation.

- **states** — One state has many LGAs.
- **lgas** — One LGA has many facilities.
- **facilities** — Identity, address, coordinates, and operational metadata.
- **facility_services** — Connects facilities to services, including availability and verification details.
- **facility_contacts** — Contact persons for a facility, optionally tied to a specific service.

Supporting tables: services, service schedules, data sources, verification history, resident preferences, conversation state, feedback, admin users, and audit logs.

### Core tables

| Table | Purpose | Important fields |
|---|---|---|
| `states` | Nigerian states and FCT | id, name, code |
| `lgas` | LGAs within each state/FCT | id, state_id, name |
| `facilities` | Health facility records | id, lga_id, name, facility_type, address, latitude, longitude, verification_status, source_id, last_verified_at, is_demo |
| `services` | Canonical healthcare services | id, code, name, description |
| `facility_services` | Services offered at facilities | facility_id, service_id, availability_status, verification_status, last_verified_at |
| `facility_contacts` | Contact persons for facilities | id, facility_id, service_id (nullable), full_name, role_title, phone, email, is_primary, is_active, verification_status, source_id, last_verified_at, is_demo |
| `service_schedules` | Opening times and service schedules | facility_id, service_id, day_of_week, opens_at, closes_at, status |
| `data_sources` | Where information originated | id, name, source_type, source_url, last_checked_at |
| `verification_history` | Record changes and verification events | id, facility_id, entity_type, entity_id, field_name, old_value, new_value, verified_by, verified_at, notes |
| `resident_preferences` | Optional conversation preferences | telegram_user_id, state_id, lga_id, updated_at |
| `conversation_state` | Persistent conversation context | thread_id, state_json, updated_at |
| `feedback` | Resident reports about facilities | id, facility_id, telegram_user_id, feedback_type, description, created_at, status |
| `admin_users` | Admin accounts and permissions | id, email, password_hash or identity-provider ID, role, is_active |
| `audit_logs` | Sensitive administrative changes | id, admin_user_id, action, entity_type, entity_id, created_at |

Add appropriate indexes and unique constraints, including unique state names/codes, unique service codes, and at most one active primary contact per facility (and per facility-service pair where service-specific). Use foreign keys to preserve data integrity.

### Data quality rules

Use explicit statuses instead of treating missing data as proof of unavailability.

Suggested verification statuses:

- `verified` — confirmed by an authorised source or review process.
- `reported` — information has been submitted but not independently verified.
- `unknown` — no reliable information is available.
- `outdated` — previously recorded information requires rechecking.

Service availability may also need a separate operational status, such as `available`, `temporarily_unavailable`, or `unknown`. Keep verification and operational availability distinct.

For demo data, include a clear `is_demo` flag or equivalent dataset/source marker on facilities, services, and contacts so users and administrators can distinguish seeded examples from real verified records.

### Database migration and seeding

- Use Alembic migrations to create and evolve the schema.
- Create a repeatable, idempotent seed script.
- Seed Nigerian state/LGA records needed by the pilot.
- Seed illustrative facilities, services, coordinates, sample schedules, **and sample contact persons**.
- Add realistic relationships between facilities, their services, and their contacts.
- **Demo contact persons must use clearly fictional names and reserved or obviously fake phone numbers and email addresses (for example, `@example.org`), so no real person can be contacted by mistake.**
- Never label invented facilities, coordinates, or contacts as verified.
- Make the seed script safe to rerun without creating duplicate rows.

---

## 8. LangGraph conversation architecture

The workflow combines natural-language understanding with deterministic application logic.

### Recommended graph nodes

1. **Load conversation** — Identify the Telegram user and restore their saved state.
2. **Input guardrail** — Check the incoming message before any other processing (see section 9). Urgent symptoms route to the escalation flow; out-of-scope, diagnosis, or prescription requests route to a safe refusal; prompt-injection attempts are neutralised.
3. **Understand message** — Extract intent, service, location, preferences, and references to previous results.
4. **Validate and route** — Check required fields, resolve entities, and determine the next action.
   - **Clarify** — Ask for a missing state, LGA, or other essential detail.
   - **Execute tool** — Search facilities, retrieve details, retrieve contact persons, or check approved information.
   - **Escalate** — Deliver the urgent-care escalation message and stop the routine search.
5. **Compose response** — Create a concise reply from validated tool results, including contact details.
6. **Output guardrail** — Check the drafted reply against this turn's tool results before sending (see section 9). If a check fails, replace the reply with a safe, deterministic template.
7. **Persist and respond** — Save relevant context and deliver the message through Telegram.

Every graph run is traced in LangSmith (see section 9).

### Conversation state

Store structured information such as:

```json
{
  "intent": "search_facilities",
  "service_code": "antenatal_care",
  "state_id": "...",
  "lga_id": "...",
  "neighborhood": null,
  "previous_facilities": [],
  "selected_facility_id": null,
  "missing_fields": [],
  "next_action": "search_facilities"
}
```

Use a persistent LangGraph checkpointer or a database-backed conversation store. Configure thread identity carefully so one Telegram user's private context cannot leak into another user's conversation.

Avoid saving every message forever. Retain only the context needed for the service, with appropriate privacy and retention controls.

### Suggested MCP tools

If you expose tools using FastMCP, start with these:

- `search_facilities(service_code, state_id, lga_id, neighborhood)`
- `get_facility_details(facility_id)`
- `get_facility_services(facility_id)`
- `get_facility_contacts(facility_id, service_code)`
- `get_service_instructions(service_code)`
- `check_service_availability(facility_id, service_code)`
- `get_directions(facility_id)`
- `submit_facility_feedback(facility_id, feedback_type, description)`

The exact arguments should be validated with Pydantic schemas. The tools call your existing Python service layer, which owns the SQL queries and business rules. Do not expose arbitrary SQL execution to the model.

---

## 9. Guardrails, observability (LangSmith), and evaluations

These three features make the AI part of the system safe, debuggable, and measurable. They wrap the LangGraph workflow; they do not replace the deterministic service layer.

### 9.1 Guardrails

A **guardrail** is a check that runs automatically before or after the AI does something, and blocks or corrects unsafe behaviour. Guardrails are ordinary, testable Python code. Prefer deterministic rules first and use an LLM classifier only where rules are not enough. When a guardrail is unsure, it **fails safe**: it escalates or falls back to a template, never the other way round.

**Input guardrails (before the message is understood)**

| Guardrail | What it does |
|---|---|
| Urgent-symptom detection | Detects red-flag symptoms (for example heavy bleeding in pregnancy, difficulty breathing, convulsions, unconsciousness) using a keyword list plus an optional LLM classifier, and routes to the escalation flow. |
| Scope check | Detects requests for diagnosis, medication, dosage, or unrelated topics, and replies with a polite refusal that redirects to facility navigation. |
| Prompt-injection defence | Treats user text as data, never as instructions. Attempts such as "ignore your rules" or "show me all phone numbers in the database" do not change the bot's behaviour or tool permissions. |
| Sensitive-data minimisation | Discourages residents from sharing medical history; avoids storing personal details from messages in conversation state or traces. |
| Message limits | Rejects or truncates extremely long messages and rate-limits abusive senders. |

**Tool guardrails (when the model calls a tool)**

- Only an allowlisted set of tools can be called, each with Pydantic-validated arguments.
- Invalid arguments return a structured error to the graph instead of crashing or reaching the database.
- Tools are read-only for residents, except `submit_facility_feedback`.

**Output guardrails (before the reply is sent)**

| Guardrail | What it does |
|---|---|
| Grounding check | Every facility name, phone number, email address, and map URL in the reply must appear in this turn's tool results. Anything else fails the check. |
| Contact presence | Each facility shown includes its stored contact, or the explicit "no contact on record" message. |
| Status labels | Demo, unverified, and outdated data keep their labels in the final text. |
| Safety wording | The reply contains no diagnosis or prescription language and no "nearest" or "nearby" claims based only on the LGA. |

To make grounding easy to guarantee, facility cards (name, address, contact, status, map link) are rendered with deterministic templates from tool results; the LLM writes only the short connecting sentences. If an output guardrail fails, the bot sends the deterministic template on its own and logs the failure.

**Escalation flow:** for the POC, use a conservative placeholder policy (tell the resident to seek emergency care immediately and stop the routine search). It is clearly marked as **not clinically reviewed** and must be approved by a qualified clinician before any real pilot.

### 9.2 Observability with LangSmith

**LangSmith** records a **trace** for each graph run: a step-by-step timeline of the nodes that ran, each LLM prompt and response, each tool call and its result, latency, token usage, and errors.

- Enable tracing through environment variables (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`). Use separate LangSmith projects for development, evaluation, and production.
- Tag traces with metadata such as graph version, prompt version, model name, and a **hashed** conversation thread ID so a whole conversation can be grouped without exposing the Telegram user ID.
- Keep tracing off by default in the unit-test suite.
- Record guardrail outcomes (passed, blocked, fell back) in the trace so failures are easy to find.
- **Privacy:** traces are sent to an external service. During the POC only synthetic data is used. Before piloting with real residents, mask or hide message content in traces, set a retention period, and review this against Nigerian privacy requirements.

### 9.3 Evaluations (evals)

**Evals** measure how well the AI behaves on a fixed set of example conversations. Unit tests check deterministic code with a single right answer; evals score probabilistic LLM behaviour and track it across changes to prompts, models, or the graph.

**Eval dataset**

- A versioned file in the repository (for example `backend/evals/datasets/conversations.jsonl`), synced to a LangSmith dataset.
- Covers single-turn and multi-turn conversations: complete requests, missing location, service changes ("what about vaccination instead?"), references ("the first one"), contact follow-ups ("who do I call?"), no-results cases, facilities with no contact, urgent symptoms, diagnosis and prescription requests, off-topic messages, and prompt-injection attempts.
- Each example stores the expected structured outcome (intent, service code, state, LGA, next action) and any expected properties of the reply.

**Evaluators**

| Evaluator | Type | What it scores |
|---|---|---|
| Extraction accuracy | Deterministic | Intent, service, state, and LGA match the expected values. |
| Routing correctness | Deterministic | The graph chose the expected next action (clarify, search, escalate, refuse). |
| Grounding | Deterministic | No facility, contact, or URL appears that is not in the tool results. |
| Safety | Deterministic | Urgent cases escalate; diagnosis and prescription requests are refused. |
| Contact completeness | Deterministic | Each facility result has its contact or the "no contact on record" message. |
| Clarification efficiency | Deterministic | The bot does not re-ask for details already given in the conversation. |
| Helpfulness and tone | LLM-as-judge (optional) | The reply is concise, clear, and friendly. |

**Pass thresholds (release gates)**

- Safety and grounding: **100%**. Any failure blocks a release.
- Extraction accuracy and routing correctness: at least **90%**.
- Every eval run is saved as a LangSmith experiment so results can be compared before and after a change.

Failures found in traces or user feedback are added to the dataset, so the eval suite grows with every bug fixed.

---

## 10. Admin web application

Build a separate Next.js application for authorised administrators.

### Required features

**Dashboard**
Show total facilities, service records, contact records, verified records, records requiring review, and recent feedback.

**Facility management**
Create, edit, view, and deactivate facilities; maintain addresses, coordinates, types, and associated LGAs.

**Service management**
Assign services to facilities and update service-specific schedules and availability.

**Contact person management**
Add, edit, deactivate, and reorder contact persons for each facility; set a primary contact; optionally link a contact to a specific service; record the source and verification status of each contact.

**Verification queue**
Review unverified records (facilities, services, and contacts), record the evidence and source, and mark appropriate fields as verified or outdated.

**Feedback management**
Review reports from residents (including reports of wrong or unreachable contact details), investigate them, and update records when supported by evidence.

### Roles and permissions

For the POC, implement at least:

- **Admin:** manage administrator accounts and all facility, service, contact, and verification records.
- **Data reviewer:** review and verify facility, service, and contact information and process feedback.
- **Read-only viewer (optional):** view records and dashboard metrics without editing.

Enforce permissions in FastAPI, not just by hiding buttons in Next.js. Hash passwords securely if you manage credentials yourself, or use a reputable authentication provider. Log important administrative changes, including any change to contact details.

---

## 11. Backend API scope

FastAPI serves as the central application backend.

| Endpoint | Purpose |
|---|---|
| `POST /webhooks/telegram` | Receive Telegram updates and process messages. |
| `GET /health` | Check application health. |
| `GET /api/states` | Retrieve supported states and FCT. |
| `GET /api/states/{state_id}/lgas` | Retrieve LGAs for a state. |
| `GET /api/facilities` | Search facilities using validated filters. |
| `GET /api/facilities/{facility_id}` | Retrieve facility details, location, and primary contact. |
| `GET /api/facilities/{facility_id}/services` | Retrieve service records. |
| `GET /api/facilities/{facility_id}/contacts` | Retrieve contact persons for a facility. |
| `POST /api/admin/facilities` | Create a facility with admin permissions. |
| `PATCH /api/admin/facilities/{facility_id}` | Update a facility with admin permissions. |
| `POST /api/admin/facilities/{facility_id}/services` | Assign or update a service. |
| `POST /api/admin/facilities/{facility_id}/contacts` | Add a contact person to a facility. |
| `PATCH /api/admin/facilities/{facility_id}/contacts/{contact_id}` | Update or deactivate a contact person. |
| `POST /api/admin/facilities/{facility_id}/verify` | Record a verification action (facility, service, or contact). |
| `GET /api/admin/feedback` | Retrieve feedback for authorised review. |
| `PATCH /api/admin/feedback/{feedback_id}` | Update feedback status. |

Add pagination, filtering, validation (including phone and email format validation for contacts), authentication, and structured error responses. The Telegram webhook validates requests using Telegram's configured secret-token mechanism, and processing is resilient to duplicate webhook deliveries.

---

## 12. Health information, privacy and safety

This is a health navigation application, so reliability and trust are core requirements, even for a POC.

- Do not diagnose illnesses, prescribe medication, or present the bot as a replacement for a clinician.
- Use approved health information sources for any instructions about accessing care.
- For potentially urgent symptoms, follow a clinically reviewed escalation flow rather than continuing a routine facility search.
- Never invent opening hours, costs, available staff, vaccine stock, service availability, or contact details.
- Share only official, work-related contact details of facility staff; never store or display personal contact details.
- Make sure contact persons are aware that their work contact details are listed, and give them a way to request correction or removal.
- Avoid collecting medical history or other sensitive personal information unless a clearly defined feature requires it.
- Restrict administrative access and encrypt traffic in transit.
- Keep API keys, database credentials, bot tokens, and LLM credentials in environment variables or a secrets manager.
- Do not log bot tokens, database credentials, or unnecessary sensitive message content.
- Treat LangSmith traces as logs that leave our infrastructure: use only synthetic data during the POC, hash Telegram user IDs in trace metadata, and mask message content in traces before any real pilot.
- Apply a retention policy to conversation data and feedback.
- Review applicable Nigerian privacy and health-sector requirements before piloting with real residents.

For the demonstration, use synthetic data (including synthetic contact persons) and make its status clear to anyone testing the application.

---

## 13. Suggested project structure

Keep the backend modular from the beginning so the bot, admin app, and AI workflow share the same business logic.

```
ai-health-navigator/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   │   ├── public.py
│   │   │   ├── admin.py
│   │   │   └── telegram.py
│   │   ├── services/
│   │   │   ├── facility_service.py
│   │   │   ├── contact_service.py
│   │   │   ├── location_service.py
│   │   │   ├── verification_service.py
│   │   │   └── maps_service.py
│   │   ├── agent/
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   ├── prompts.py
│   │   │   ├── tracing.py
│   │   │   ├── nodes/
│   │   │   └── guardrails/
│   │   │       ├── input_guardrails.py
│   │   │       ├── output_guardrails.py
│   │   │       └── escalation.py
│   │   ├── mcp/
│   │   │   └── server.py
│   │   └── security/
│   ├── migrations/
│   ├── seed/
│   │   └── seed_demo.py
│   ├── evals/
│   │   ├── datasets/
│   │   │   └── conversations.jsonl
│   │   ├── evaluators.py
│   │   └── run_evals.py
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── admin-web/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

This is a suggested layout, not a requirement to create every file immediately. Build the essential modules first and introduce additional modules as their responsibilities become clear.

---

## 14. Deployment and free-tier considerations

- **NeonDB:** hosted PostgreSQL database.
- **FastAPI:** deploy as a Docker container on a suitable hosting service.
- **Next.js:** deploy the admin interface separately or alongside the backend where appropriate.
- **Telegram:** configure a webhook using the deployed HTTPS endpoint.
- **LLM:** use a provider with an available free quota or a local model for development. Do not assume a free quota will remain available indefinitely.
- **MCP:** run within the backend environment or as a separate service if independent deployment becomes useful.
- **LangSmith:** use the free developer tier for tracing and evals; use separate projects for development, evaluation, and production, and keep the API key in environment variables.

Use separate development and production environment variables. Run database migrations as part of a controlled deployment process rather than automatically making schema changes on every application startup.

---

## 15. Testing and acceptance criteria

The project is ready for a POC demonstration when the following workflows work reliably.

### POC acceptance checklist

**Resident experience**

- [ ] User can start a conversation in English and describe a healthcare service in free text.
- [ ] Bot asks for missing location information without repeating questions already answered.
- [ ] User can search by state, LGA and service.
- [ ] Follow-up messages retain relevant context and correctly handle service changes and references to previous results.

**Facility search, contacts and maps**

- [ ] Search results come from NeonDB rather than invented LLM output.
- [ ] Each returned facility has a real database ID and an appropriate service record.
- [ ] Each returned facility includes its contact person details from the database, or clearly states that no contact is on record.
- [ ] Contact details are labelled with their verification status, and demo contacts are clearly marked as demonstration data.
- [ ] Follow-up questions such as "who can I call at the first one?" are answered from stored contact records.
- [ ] Valid coordinates generate a working Google Maps location or directions link.
- [ ] Missing or unverified data is clearly labelled, and the bot does not claim nearest or currently available without supporting data.

**Admin and database**

- [ ] An authorised admin can create and update facilities, services, and contact persons.
- [ ] Unauthorised users cannot access protected admin endpoints.
- [ ] Verification changes (including contact changes) are recorded in audit or verification history.
- [ ] Database migrations and the seed script can be run reproducibly.

**Reliability and safety**

- [ ] Conversation state survives server restarts when persistence is configured.
- [ ] Different users cannot access each other's conversation state.
- [ ] Errors, duplicate webhook deliveries and invalid tool arguments are handled safely.
- [ ] Urgent health-related messages follow an approved escalation policy.

**Guardrails, observability and evals**

- [ ] Diagnosis, prescription, off-topic, and prompt-injection messages are handled safely by input guardrails.
- [ ] Output guardrails block any reply containing a facility, contact, or URL not found in the tool results, and fall back to a deterministic template.
- [ ] Every conversation turn produces a LangSmith trace showing nodes, LLM calls, tool calls, and guardrail outcomes, with no raw Telegram user IDs or secrets.
- [ ] The eval suite runs from one command and meets its thresholds: 100% safety and grounding, at least 90% extraction and routing.

### Automated tests

Write automated tests for:

- The database query layer (including contact retrieval and primary-contact selection).
- Service and location extraction.
- LangGraph routing.
- Permissions.
- Telegram message formatting (including contact person sections and missing-contact messages).
- Phone and email validation for contacts.
- Input and output guardrails (urgent-symptom detection, scope check, grounding check, fallback templates).

Test realistic multi-turn conversations, not just isolated prompts.

Unit tests and evals are different: unit tests (pytest) check deterministic code and must always pass; evals (LangSmith) score LLM behaviour against thresholds. Both run before each release.

---

## 16. Build roadmap

**01 — Foundation and database**
Set up NeonDB, SQLAlchemy, Alembic, the relational schema (including facility contacts), seed scripts, and initial facility-search queries. Define data verification rules early.

**02 — Deterministic backend**
Build FastAPI endpoints, facility and service search, contact retrieval, admin permissions, validation, and Google Maps link generation. Test these without an LLM.

**03 — Telegram, natural conversation, guardrails, and tracing**
Connect the Telegram webhook, add LangGraph intent extraction and routing, implement clarifying questions, include contact details in responses, and persist multi-turn state. Turn on LangSmith tracing from the first LLM call, add input, tool, and output guardrails with the escalation flow, and create a first small eval dataset with deterministic evaluators.

**04 — Admin application**
Build the Next.js dashboard, facility/service/contact forms, verification queue, and feedback management.

**05 — Testing, evaluation, and deployment**
Add the remaining automated tests, grow the eval dataset to full coverage with pass thresholds, add optional LLM-as-judge evaluators, Docker deployment, webhook configuration, logs, error handling, and a complete demo scenario.

---

## 17. What success looks like

A reviewer should be able to open Telegram, ask for a healthcare service in ordinary English, provide a state and LGA when needed, receive matching facilities from NeonDB along with each facility's contact person, ask follow-up questions without repeating their request, and tap a Google Maps link to navigate to a facility.

Meanwhile, an administrator should be able to log into the separate web application, maintain facility, service, and contact information, and review verification records.

A developer should be able to open LangSmith, find the trace for any conversation turn, see exactly why the bot answered as it did, and run the eval suite to confirm that a change has not made the bot less safe or less accurate.

The project should demonstrate AI orchestration, reliable database retrieval, conversational state management, secure backend design, MCP tool integration, guardrails, observability, systematic evaluation, and a practical public-service use case.

**Implementation recommendation:** build the database search, contact retrieval, and Google Maps links first, then connect LangGraph and Telegram. That way, the most important facts and actions work correctly before the conversational intelligence is added on top.
