"""Lead qualification and intelligence agent.

This module implements a simple reference version of the NXTUTORS Lead Qualification &
Intelligence Agent.  It accepts semi‑structured lead information and outputs a
fully structured JSON object conforming to the specification defined in the
founder’s master prompt.  The logic here uses heuristics to infer intent,
urgency, budget and next steps; in a production system these heuristics would
be replaced by a more sophisticated scoring model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re


@dataclass
class LeadQualificationAgent:
    """Agent class for qualifying and routing NXTUTORS leads."""

    # thresholds for quality scoring
    high_intent_threshold: int = 80
    medium_intent_threshold: int = 60
    low_intent_threshold: int = 40

    def _parse_budget(self, budget_str: Optional[str]) -> Tuple[str, str]:
        """Infer a budget range and category from a free‑form budget string.

        Returns a tuple of `(range_str, category)` where `range_str` is the parsed
        monetary range and `category` is one of ``low``, ``medium`` or ``high``.
        If no budget is provided, both values default to "Unknown".
        """
        if not budget_str:
            return "Unknown", "Unknown"

        # extract numbers (including thousands separators and currency symbols)
        numbers = re.findall(r"\d+(?:,\d{3})*", budget_str)
        if numbers:
            # convert comma‑separated numbers to integers
            amounts = [int(num.replace(",", "")) for num in numbers]
            low = min(amounts)
            high = max(amounts)
            # classify category heuristically (these buckets are domain‑specific)
            if high <= 3000:
                category = "Low"
            elif high <= 8000:
                category = "Medium"
            else:
                category = "High"
            range_str = f"\u20b9{low}–\u20b9{high}" if low != high else f"\u20b9{low}"
            return range_str, category
        return "Unknown", "Unknown"

    def _determine_urgency(self, urgency_str: Optional[str]) -> str:
        """Classify urgency into Immediate, Short‑Term or Long‑Term."""
        if not urgency_str:
            return "Long‑Term"
        # look for numbers of days or hours
        days_match = re.search(r"(\d+)\s*(?:day|days)", urgency_str, re.IGNORECASE)
        hours_match = re.search(r"(\d+)\s*(?:hour|hours)", urgency_str, re.IGNORECASE)
        if hours_match:
            hours = int(hours_match.group(1))
            return "Immediate" if hours <= 48 else "Short‑Term"
        if days_match:
            days = int(days_match.group(1))
            if days <= 2:
                return "Immediate"
            if days <= 7:
                return "Short‑Term"
        return "Long‑Term"

    def _assess_subject_complexity(self, subjects: Optional[List[str]]) -> str:
        """Estimate subject complexity based on course names."""
        if not subjects:
            return "Unknown"
        high_complexity_keywords = {"JEE", "NEET", "IIT", "IB", "IGCSE"}
        medium_complexity_keywords = {"Math", "Physics", "Chemistry", "Biology"}
        for sub in subjects:
            for keyword in high_complexity_keywords:
                if keyword.lower() in sub.lower():
                    return "High"
        for sub in subjects:
            for keyword in medium_complexity_keywords:
                if keyword.lower() in sub.lower():
                    return "Medium"
        return "Low"

    def _compute_location_feasibility(self, location: Optional[str], mode: Optional[str]) -> int:
        """Calculate a rough feasibility score based on location granularity and mode.

        In this example, locations containing keywords like "sector", "society",
        or specific micro‑neighbourhoods are considered more precise and thus
        easier to match with home tutors.  Online mode is assumed always
        feasible (score 100).
        """
        if not location:
            return 50  # neutral baseline
        if mode and mode.lower() == "online":
            return 100
        loc_lower = location.lower()
        if any(term in loc_lower for term in ("sector", "society", "block")):
            return 80
        if any(term in loc_lower for term in ("city", "town", "district")):
            return 60
        return 50

    def qualify_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify the incoming lead and return a structured intelligence dict."""
        lead_id = lead.get("lead_id") or ""
        mode = lead.get("mode_preference") or lead.get("mode") or "Unknown"
        subjects = lead.get("subjects") or []
        budget = lead.get("budget") or lead.get("budget_range")
        urgency = lead.get("urgency")

        # Compute various attributes
        budget_range, budget_category = self._parse_budget(budget)
        urgency_level = self._determine_urgency(urgency)
        subject_complexity = self._assess_subject_complexity(subjects)
        location_feasibility_score = self._compute_location_feasibility(lead.get("location"), mode)

        # Start with a base quality score
        quality_score = 50
        reasoning_lines: List[str] = []

        # Adjust score based on budget category
        if budget_category == "Low":
            quality_score += 5
            reasoning_lines.append("Low budget implies affordability; small boost.")
        elif budget_category == "Medium":
            quality_score += 10
            reasoning_lines.append("Medium budget suggests moderate affordability.")
        elif budget_category == "High":
            quality_score += 20
            reasoning_lines.append("High budget indicates strong ability to pay.")

        # Urgency bonus
        if urgency_level == "Immediate":
            quality_score += 20
            reasoning_lines.append("Immediate urgency indicates high intent.")
        elif urgency_level == "Short‑Term":
            quality_score += 10
            reasoning_lines.append("Short‑term urgency indicates medium intent.")

        # Subject complexity influences quality
        if subject_complexity == "High":
            quality_score += 15
            reasoning_lines.append("High complexity subjects require specialized tutors.")
        elif subject_complexity == "Medium":
            quality_score += 5
            reasoning_lines.append("Medium complexity subjects are common but significant.")

        # Feasibility adjustments
        if location_feasibility_score >= 80:
            quality_score += 10
            reasoning_lines.append("Precise location makes home tutoring feasible.")
        elif location_feasibility_score <= 60:
            quality_score -= 5
            reasoning_lines.append("Generic location lowers match confidence.")

        # Bound score between 0 and 100
        quality_score = max(0, min(100, quality_score))

        # Determine intent level label
        if quality_score >= self.high_intent_threshold:
            lead_quality_label = "High"
            intent_level = "High Intent"
        elif quality_score >= self.medium_intent_threshold:
            lead_quality_label = "Medium"
            intent_level = "Medium Intent"
        elif quality_score >= self.low_intent_threshold:
            lead_quality_label = "Low"
            intent_level = "Low Intent"
        else:
            lead_quality_label = "Invalid"
            intent_level = "Low Intent"

        # Decide recommended next agent based on score and urgency
        if lead_quality_label == "High":
            if urgency_level == "Immediate":
                recommended_agent = "Tutor Matching Agent"
            else:
                recommended_agent = "Sales Closure Agent"
        elif lead_quality_label == "Medium":
            recommended_agent = "Academic Counselor Agent"
        elif lead_quality_label == "Low":
            recommended_agent = "WhatsApp Nurture Agent"
        else:
            recommended_agent = "Archive / Ignore Agent"

        # Confidence is proportional to how far the score is from the median (50)
        confidence_in_recommendation = round(abs(quality_score - 50) / 50 * 100)

        # Compose reasoning summary
        reasoning_summary = "; ".join(reasoning_lines) or "Lead evaluated with default heuristics."

        # Memory tags for analytics (simple tags based on categories)
        memory_tags: List[str] = []
        memory_tags.append(f"budget:{budget_category.lower()}")
        memory_tags.append(f"urgency:{urgency_level.lower()}")
        memory_tags.append(f"complexity:{subject_complexity.lower()}")
        memory_tags.append(f"intent:{intent_level.lower().replace(' ', '-')}")
        result: Dict[str, Any] = {
            "lead_id": lead_id,
            "lead_quality_score": quality_score,
            "lead_quality_label": lead_quality_label,
            "intent_level": intent_level,
            "urgency_level": urgency_level,
            "budget_range_inferred": budget_range,
            "preferred_mode": mode,
            "subject_complexity": subject_complexity,
            "location_feasibility_score": location_feasibility_score,
            "recommended_next_agent": recommended_agent,
            "confidence_in_recommendation": confidence_in_recommendation,
            "reasoning_summary": reasoning_summary,
            "memory_tags": memory_tags,
            "human_attention_required": False if lead_quality_label in {"High", "Medium"} else True,
        }

        return result
