# NXTUTORS Lead Qualification & Intelligence Agent

This repository contains a reference implementation of an AI‑powered lead qualification agent used within the **NXTUTORS** multi‑agent architecture.  Its goal is to convert raw student/parent enquiries into structured, decision‑ready intelligence that downstream agents can act on.

The agent ingests semi‑structured lead data (such as student name, class, board, subjects, location, budget and urgency) and produces a normalized JSON output with a quality score, intent level, urgency category, inferred budget range and a recommended next agent.  The heuristics encoded here are intentionally simple; a production system would include more sophisticated natural language processing, dynamic scoring models and integration with RAG/memory services.

## Features

* **Lead scoring** – Assigns a lead quality score between 0‑100 based on intent, urgency and budget.
* **Intent & urgency detection** – Flags whether a lead is high, medium or low intent and whether the request is immediate, short‑term or long‑term.
* **Budget inference** – Parses textual budget ranges and categorizes them into low/medium/high buckets.
* **Subject & board complexity** – Recognizes special cases such as JEE/NEET that require senior tutors or counselors.
* **Routing recommendations** – Suggests whether the lead should be routed to the tutor matching agent, an academic counselor, nurtured via WhatsApp or archived.
* **Explainability** – Returns a short, human‑readable reasoning summary alongside the machine‑readable output.

## Versioned prompts (v1 → v3 evolution)

This repository models the evolution of the lead‑qualification prompt into three internal versions. The current `agent.py` behavior reflects the v3 direction, while keeping the earlier versions for traceability and iteration.

* **v1 – Baseline qualification**
  * Core extraction of intent, urgency, budget, subject complexity.
  * Simple routing between matching, counseling, nurture, or archive.
  * Minimal memory tags (budget, urgency, complexity, intent).
* **v2 – Operational intelligence**
  * Added hyper‑local feasibility scoring for home vs online.
  * Introduced more explicit explainability lines per scoring factor.
  * Standardized agent routing labels and confidence scoring.
* **v3 – Scalable system intelligence**
  * Enforced JSON‑only output discipline with CRM‑ready fields.
  * Expanded lead scoring into a consistent, explainable formula.
  * Added contracts for agent‑to‑agent handoffs and feedback loops.

## Scoring formula logic

The current scoring model is intentionally transparent so downstream agents can explain and audit decisions. The `LeadQualificationAgent` uses a base score of **50** and adjusts based on signal strength:

| Signal | Condition | Adjustment |
| --- | --- | --- |
| Budget category | Low / Medium / High | +5 / +10 / +20 |
| Urgency | Immediate / Short‑Term | +20 / +10 |
| Subject complexity | High / Medium | +15 / +5 |
| Location feasibility | ≥ 80 / ≤ 60 | +10 / −5 |

The score is clamped to **0–100**. Intent labels map to thresholds:

* **High Intent**: ≥ 80
* **Medium Intent**: 60–79
* **Low Intent**: 40–59
* **Invalid**: < 40

Routing uses the intent label and urgency: high‑intent immediate leads go to **Tutor Matching**, high‑intent non‑immediate to **Sales Closure**, medium intent to **Academic Counselor**, low intent to **WhatsApp Nurture**, otherwise **Archive / Ignore**.

## Agent‑to‑agent contract definitions

Downstream agents depend on predictable outputs. Each handoff assumes the following contract:

* **Tutor Matching Agent**
  * Trigger: `lead_quality_label = High` and `urgency_level = Immediate`.
  * Must receive: location details, preferred mode, subjects, urgency.
* **Sales Closure Agent**
  * Trigger: `lead_quality_label = High` and `urgency_level != Immediate`.
  * Must receive: intent summary, budget tier, board/class/subject mix.
* **Academic Counselor Agent**
  * Trigger: `lead_quality_label = Medium`.
  * Must receive: subject complexity, exam signals, support gaps.
* **WhatsApp Nurture Agent**
  * Trigger: `lead_quality_label = Low`.
  * Must receive: tone hints from reasoning summary and memory tags.
* **Human Override Agent**
  * Trigger: `human_attention_required = True` or conflicts in inputs.
  * Must receive: full lead payload and reasoning summary.
* **Archive / Ignore Agent**
  * Trigger: `lead_quality_label = Invalid` or no meaningful signals.
  * Must receive: lead_id, minimal audit notes.

## CRM field mapping

The output payload is designed to map cleanly into CRM fields.

| Agent output field | CRM field name | Notes |
| --- | --- | --- |
| `lead_id` | `lead_id` | Unique lead key |
| `lead_quality_score` | `qualification_score` | 0–100 integer |
| `lead_quality_label` | `qualification_label` | High/Medium/Low/Invalid |
| `intent_level` | `intent_level` | Human‑readable label |
| `urgency_level` | `urgency_level` | Immediate/Short‑Term/Long‑Term |
| `budget_range_inferred` | `budget_range` | Parsed currency range |
| `preferred_mode` | `preferred_mode` | Home/Online/Hybrid/Unknown |
| `subject_complexity` | `subject_complexity` | Low/Medium/High/Unknown |
| `location_feasibility_score` | `location_feasibility_score` | 0–100 integer |
| `recommended_next_agent` | `next_agent` | Routing decision |
| `confidence_in_recommendation` | `routing_confidence` | 0–100 integer |
| `reasoning_summary` | `qualification_notes` | Short narrative |
| `memory_tags` | `memory_tags` | Array of tags |
| `human_attention_required` | `needs_human_review` | Boolean |

## Auto‑learning feedback loops

The design assumes periodic updates to improve scoring and routing accuracy:

1. **Outcome capture** – record final conversion status and tutor assignment outcomes against `lead_id`.
2. **Signal drift checks** – compare actual conversion rates against `lead_quality_label` cohorts.
3. **Threshold tuning** – adjust budget/urgency/complexity weights when false positives/negatives grow.
4. **Tag enrichment** – expand `memory_tags` with new high‑signal dimensions (e.g., exam month, parent involvement).
5. **Reroute audits** – track leads that required human override to refine routing triggers.

## Repository contents

```
.
├── agent.py      # main module with the LeadQualificationAgent class
├── example_input.json  # sample lead input for testing
├── example_output.json # sample agent output based on the example input
└── README.md    # project overview and usage instructions
```

## Usage

The module exposes a `LeadQualificationAgent` class with a single method `qualify_lead()` that accepts a dictionary representing the raw lead data.  The method returns a dictionary with the fields mandated by the NXTUTORS specification.

```python
from agent import LeadQualificationAgent

raw_lead = {
    "lead_id": "1234",
    "student_name": "Aarav",
    "role": "Parent",
    "class": "9",
    "board": "CBSE",
    "subjects": ["Math", "Science"],
    "location": "Gurugram Sector 56",
    "mode_preference": "home",
    "urgency": "3 days",
    "budget": "₹3000 per month",
    "language_preference": "English",
    "source": "Website Enquiry"
}

agent = LeadQualificationAgent()
result = agent.qualify_lead(raw_lead)
print(result)
```

The `example_input.json` and `example_output.json` files provide a reference input and corresponding output to help you understand how the heuristics map to the JSON schema.

## Disclaimer

This project is a demonstration of how the NXTUTORS lead qualification agent can be structured.  It is **not** production ready.  The heuristics for scoring, budgeting, complexity and routing are simplistic and meant to illustrate the specification rather than guarantee optimal business outcomes.  In a real deployment, these rules would be replaced with data‑driven models, continuous learning and deeper integrations with the broader NXTUTORS platform.
