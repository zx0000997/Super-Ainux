# Super Ainux System (SAS) — System Development Specification

**Version**: 1.0  
**Audience**: System architects, backend/infrastructure engineers, AI engineers, security/compliance, frontend (task board)  
**Goal**: After reading this document, engineers can decompose milestones, APIs, data models, and implementation tasks.

---

## 1. Scope and Conventions

### 1.1 What This Document Defines

- Product boundaries of SAS, subsystem decomposition, and the **task-first** operational model.  
- **Dual-LLM governance** (Operator / Supervisor): responsibilities, delegated permissions, and review-before-execute flow.  
- Local data plane (document ingest, retrieval, templates), a **unified audit log**, and task–data binding.  
- Blocking scenarios (credentials, quota/payment, template/solution selection), notification channels, and deliverable specifications.  
- Userland/platform requirements on top of a **Linux distribution** (this spec does not replace generic kernel build guides; see `OS_DEVELOPMENT_GUIDE.md` in the repo for kernel baseline).

### 1.2 What This Document Does Not Replace

- Concrete language/framework choices (freeze via ADRs during implementation).  
- Vendor-specific details of third-party model APIs (follow provider docs as they evolve).

### 1.3 Glossary

| Term | Definition |
|------|------------|
| **SAS** | Super Ainux System: a Linux-based system where **AI is the primary operator** and humans provide requirements and select among options. |
| **Operator** | Operator AI: produces Plans and executes tasks; **must not** hold arbitrary delete privileges; **must not** write directly to the audit log. |
| **Supervisor** | Supervisor AI: reviews/modifies Plans, grants temporary capabilities, participates in completion verification; **must use a heterogeneous model** vs Operator (different provider or model family). |
| **Task** | First-class unit of work; reads/writes default to **`task_id` scope**. |
| **Approved Plan Package** | Immutable, hashed artifact approved by Supervisor—the **only** executable plan. |
| **Audit Log** | Append-only event bus: supervision grants, task transitions, delete proposals, deliverables. |
| **Information Organization** | Ingest, extract, index, scheduled housekeeping, deduplication proposals. |
| **User Portrait** | Multi-dimensional profile for LLM context; may be shared for a short time with explicit policy. |
| **Task Board** | Stable human control plane: observe tasks, notifications, deliveries (**not** a mandatory per-step approval gate). |

---

## 2. Vision and Goals

### 2.1 Product Statement

SAS runs on **x86_64** (typical: **home mini-server**) on top of a **Linux kernel**. The **primary actor is AI** (Operator); **another heterogeneous AI** (Supervisor) provides governance. Humans contribute requirements and **solution selection**, not routine “click to approve.”

### 2.2 Engineering Success Criteria

- **Review before execute**: any production-impacting change must originate from an **Approved Plan Package**.  
- **Auditable**: grants, transitions, delete proposals, and deliverables are traceable through a **single Audit Log**.  
- **Task binding**: business writes and default retrieval are scoped by **`task_id`** (see Section 7 for exceptions).  
- **Local recovery**: failures can be rolled back via snapshots/baseline images (online models/repos allowed; **offline operation not required**).  
- **Data preference order** during execution: **ephemeral user input > local data from newest to oldest > public internet data**.

---

## 3. Architectural Principles

1. **Mechanism over advice**: supervision is implemented as services and policy, not a “second chat personality.”  
2. **Heterogeneous dual-brain**: Operator and Supervisor **must not** share the same model lineage (enforced in configuration).  
3. **No delete for Operator**: deletes go through **supervisory review + trusted jobs**.  
4. **Tasks over files**: the human contract is task-centric; files are execution/delivery artifacts.  
5. **Single audit truth**: one **Audit Log** for authorization, task machine, deletes, and deliveries.  
6. **Ingest then retrieve**: inbound documents land in local stores before AI retrieval; **external-facing files are generated mainly at delivery time** (plus messages/email).

---

## 4. System Context

```
[Human] -- requirements / solution selection --> [Task Board / Mobile]
                                                  |
[AI Operator] <-- controlled execution --> [SAS Core Services]
[AI Supervisor] <-- review / authorize -----> [SAS Core Services]

[SAS] <--> [Local User DB: text / media / file storage]
[SAS] <--> [Online repos: tools / document templates / skills]
[SAS] <--> [Public internet data]
[SAS] --> [Output: documents / email / media / broadcast]
```

### 4.1 Deployment Assumptions

- **CPU**: x86_64.  
- **Network**: public model APIs and online repositories are allowed (**offline operation not required**).  
- **Privacy**: outbound data to model vendors is allowed subject to user policy and compliance settings.

---

## 5. Logical Architecture — Subsystems

### 5.1 Supervision Subsystem

**Responsibilities**

- Dual-AI coordination: **review-before-execute**; grant and revoke temporary authorization.  
- Control database privileges: after Plan approval, Supervisor-side logic issues **time-limited, revocable** tokens (or equivalent) to Operator.  
- **Authorization model (fixed)**  
  - After approval: Operator may **insert**, **query** (implement as **task-scoped first**—avoid “read entire corpus”), and **update** relevant data.  
  - Operator **does not** have delete privileges.  
- **Deletes & dedup**: Information Organization raises **delete / logical-delete proposals** → supervisory review → executed by a **non-Operator** trusted worker → Audit entry.

**Deliverables**

- Authorization APIs: `grant` / `revoke` / `renew` (scope + TTL).  
- Structured rejection/modification reason codes for the task machine and task board.

### 5.2 Task Subsystem

**Responsibilities**

- Task lifecycle and state machine.  
- Collect user intent + relevant portrait dimensions → Operator builds **Plan** → Supervisor **reviews/modifies** → **Approved Plan Package** → **execute approved package only**.  
- Execution: fetch **tools, document templates, skills** from online repos; if paid resources are needed → **quota/policy** (Section 9); if multiple templates → **selection policy** (Section 9.3).  
- Data order: **ephemeral input > local newest-first > internet**.  
- Failures: escalate to Supervisor per policy (re-plan / constrain / abort—configurable).  
- Completion: Supervisor **verifies actual completion**; if not met, return work to Operator (configure **max iterations/timeouts** to prevent infinite loops).  
- **Delivery**: messages, email, files, etc.; log to Audit.

**Reference states**

`New` → `Planning` → `PendingReview` → `Approved` → `Executing` → `Verifying` → `Completed` → `Delivered`  
(Failure/rollback/blocking states: Section 8)

**Deliverables**

- Task APIs: create, query, transition, `task_id` binding.  
- Versioned Plans and Approved Plan Packages with hash verification.  
- Executor accepting **only** commands bound to the approved package hash (immutable artifact).

### 5.3 Information Organization Subsystem

**Responsibilities**

- Ingest: **documents (PDF/Office primary)**, text, multimedia → extract and archive.  
- Long text into **`sa_file`** (or equivalent); index for retrieval and citations.  
- Layout/template metadata into **`sa_template`** (use consistent *template* naming).  
- Store media on local filesystem with timestamps; persist associations in DB.  
- **Scheduled housekeeping** (e.g., daily, configurable): dedup finds redundant rows → **delete proposal** → **supervisory review** → **logical delete** (prefer non-physical).

**Retrieval (fixed)**

- For document-heavy workloads: **hybrid retrieval** (keyword/BM25/full-text + optional vectors) + metadata filters; return **citation anchors** (page/chunk IDs).  
- Default: feed models **top-K chunks**, not whole corpora.

### 5.4 Analysis Subsystem

**Responsibilities**

- Incrementally refine **multi-dimensional user portraits** from tasks and feedback, as structured LLM input (instead of unstructured “long memory” dumps).  
- **Dimensions include** (non-exhaustive): basic demographics; visual preferences (color, layout, shape); expression preferences.  
- **Short-lived sharing**: portrait slices may be shared with other users with **scope, TTL, revocation, and audit**.

### 5.5 Advanced Log / Unified Audit

**Responsibilities**

- **Append-only** audit bus, including at minimum:  
  - Supervision: **grants/revokes/policy changes/rejections**  
  - Tasks: **state transitions** (actor: system / operator_agent / supervisor_agent / policy)  
  - Data governance: **delete proposals, review outcomes, logical-delete execution**  
  - Delivery: **artifact generation, outbound sends (email/message/file path or object key), content hashes**

**Constraints**

- Operator processes **do not** write Audit directly; trusted services append events.  
- Link to **notification delivery** via shared `event_id` for idempotency and tracing.

### 5.6 Supporting Modules

| Module | Responsibility |
|--------|----------------|
| **Task Board (Web/desktop)** | Task list, status, blocking reasons, notifications, delivery inbox; optional solution comparison (humans may choose, but no mandatory per-step click). |
| **Mobile app** | Same information architecture as board; push notifications. |
| **AI-dedicated browser** | Controlled web access; must align with supervision and Audit. |
| **Mail server / SMTP** | Outbound email; may share infrastructure with notifications. |
| **Notification subsystem** | In-app notifications + mobile/email push for credentials/quota/selection events. |

---

## 6. Data Model Essentials

### 6.1 `task_id` Everywhere

- **Default**: task-generated writes/changes must include `task_id`.  
- **Default retrieval filter**: `task_id`-visible set + policy-allowed shared/global archives.  
- **Exception**: pre-task ingest may have `task_id IS NULL` but must carry **`ingest_batch_id` / `source_id`**; later **link** operations attach `task_id` and are audited.

### 6.2 Core Tables (logical names)

- `tasks`: state, priority, acceptance criteria refs, approved package hash.  
- `sa_file`: extracted text, chunks, index versions.  
- `sa_template`: template/layout metadata.  
- `media_objects`: paths, hashes, timestamps, links.  
- `user_profile`: portrait dimensions and versions.  
- `audit_events`: append-only payloads; hash chain recommended.  
- `quota_ledger`: balance, holds, charges, manual top-ups (MVP).

### 6.3 Approved Plan Package

Must include:

- `plan_id`, `task_id`, **content hash**, Supervisor approval marker, TTL policy.  
- **Serialized action list**: packages, services, containers, file generation, external APIs.  
- **Acceptance criteria**: machine-checkable checks (probes, queries, file hashes).  
- **Rollback hints**: snapshot ID or baseline ID (aligned with local recovery).

---

## 7. Workflow — Review Before Execute

1. Operator produces a **Plan** (not directly executable as-is).  
2. Supervisor **reviews/modifies** and emits an **Approved Plan Package**.  
3. Supervision **grants** scoped, time-limited authorization.  
4. Executor runs **only** the approved package; mid-flight intent changes require a **new** package.  
5. Verifying: collect an **evidence bundle** (logs, command results, artifact hashes, cited chunks).  
6. Supervisor **completion check**; then **deliver** and audit.

---

## 8. Blocking Events and Policies

### 8.1 Payment / Quota (MVP)

- **MVP**: **quota ledger + manual top-up** (no real-time payment gateway).  
- **Policies**: users may configure **micropay** (future); or **free-only** (Plans must reject paid dependencies early).  
- **Pre-authorize holds** before paid steps; on failure → `BlockedPayment` or automatic Plan rewrite.

### 8.2 Selection (templates / multiple options)

- Configurable: **auto via portrait** or **prompt user** (board/push).  
- **Timeout default**: **auto-select**; recommended tie-break: portrait fit > lowest cost (free first) > lowest risk > recently used.

### 8.3 Missing Credentials

- State: `BlockedCredential`; **notify** user (board + app/email).  
- Audit records `credential_type` and retry/backoff policy.

---

## 9. Notifications and Delivery

- **Channels**: in-board notifications are **canonical**; outbound **app/email** (idempotent, traceable).  
- **Formats**: messages, email, files, broadcast; **new external files are primarily produced at delivery**.  
- Deliverables must link `task_id`, approved package hash, and artifact hashes.

---

## 10. Security — Minimum Threat Model

- **Heterogeneous models** reduce single-vendor key compromise of both brains; separate credential stores.  
- **Least privilege**: query/update grants default to **task scope**.  
- **Prompt injection**: separate untrusted user content from system instructions; tool calls originate from approved packages.  
- **Home server exposure**: firewall, minimal ports, split admin plane (detail during hardening).

---

## 11. Observability and Operations

- **Metrics**: task latency, block rates, retrieval latency, model API errors, quota burn.  
- **Logging**: separate application logs from **Audit**; tamper resistance (permissions + append-only/hash chain).  
- **Backup**: user DB + Audit retention/backup policy.

---

## 12. Implementation Roadmap (Suggested)

| Phase | Deliverable |
|-------|-------------|
| **M0** | Baseline Linux image, single-node deployment, secrets/config management |
| **M1** | Task table + state machine APIs; Audit skeleton; stub Operator/Supervisor adapters |
| **M2** | Information Organization: PDF/Office extract, `sa_file` chunking, hybrid retrieval |
| **M3** | Approved packages + executor sandbox; supervision tokens |
| **M4** | Task board + notifications; quota MVP; blocking-state integration |
| **M5** | Delivery pipeline (email/files); automated completion checks |
| **M6** | Portrait + sharing; dedup delete proposal end-to-end |

---

## 13. Relationship to Existing Repo Docs

- **`OS_DEVELOPMENT_GUIDE.md`**: Linux kernel download, build, and generic rootfs/bootloader guidance as **OS baseline**.  
- **This document**: SAS **platform/application** specification—orthogonal and complementary to kernel work.

---

## 14. Revision History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-03-30 | Initial release aligned with architecture discussions and mind map |

---

*License: follow the repository root `LICENSE` (e.g., Apache-2.0) when added.*
