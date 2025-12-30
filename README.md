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
