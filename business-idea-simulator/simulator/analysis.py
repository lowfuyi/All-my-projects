"""Post-failure root-cause analysis (rule 5: trigger a root-cause analysis
when a business fails).

Looks at *why* an idea failed - which stress-event traits hit it hardest,
and whether its own cost/margin structure was already fragile - and turns
that into a short list of risk-trait tags for the idea selector to steer
away from on the next iteration.
"""

from collections import Counter
from typing import List

from .events import EVENT_LIBRARY
from .ideas import BusinessIdea
from .models import IdeaOutcome, RootCauseReport

_EVENT_TRAIT_MAP = {event.name: event.trait_key for event in EVENT_LIBRARY}

_THIN_MARGIN_THRESHOLD = 0.15  # avg net margin below this is "thin"
_HIGH_FIXED_COST_RATIO = 0.35  # fixed costs above this fraction of avg revenue is "high"
_EXPENSIVE_CAC_RATIO = 0.4  # CAC above this fraction of unit price is "expensive"


class RootCauseAnalyzer:
    def analyze(self, idea: BusinessIdea, outcome: IdeaOutcome) -> RootCauseReport:
        primary_causes: List[str] = []
        risk_tags_to_avoid: List[str] = []

        if outcome.outcome == "bankrupt":
            primary_causes.append(
                "Cash reserves were depleted faster than capital injections could offset losses."
            )
        elif outcome.outcome == "negative_streak":
            primary_causes.append(
                f"Operating net profit stayed negative for {outcome.failure_streak_threshold} "
                "consecutive months, the failure threshold for this run."
            )

        event_counts = Counter(outcome.triggered_event_names)
        trait_pressure: Counter = Counter()
        for name, count in event_counts.items():
            trait_key = _EVENT_TRAIT_MAP.get(name)
            if trait_key:
                trait_pressure[trait_key] += count

        for trait_key, count in trait_pressure.most_common(3):
            risk_tags_to_avoid.append(trait_key)
            primary_causes.append(
                f"Recurring stress from '{trait_key.replace('_', ' ')}'-related events ({count}x)."
            )

        months = outcome.months
        if months:
            avg_revenue = sum(m.revenue for m in months) / len(months)
            avg_net_profit = sum(m.net_profit for m in months) / len(months)
            avg_margin = (avg_net_profit / avg_revenue) if avg_revenue > 0 else -1.0

            if avg_margin < _THIN_MARGIN_THRESHOLD:
                risk_tags_to_avoid.append("capital_intensity")
                primary_causes.append(
                    f"Average operating margin was thin ({avg_margin:.0%}), leaving little "
                    "buffer against shocks."
                )
            if avg_revenue > 0 and (idea.fixed_costs / avg_revenue) > _HIGH_FIXED_COST_RATIO:
                risk_tags_to_avoid.append("capital_intensity")
                primary_causes.append(
                    "Fixed monthly overhead was high relative to typical revenue."
                )

        if idea.unit_price > 0 and (idea.cac / idea.unit_price) > _EXPENSIVE_CAC_RATIO:
            risk_tags_to_avoid.append("ad_dependency")
            primary_causes.append(
                "Customer acquisition cost was expensive relative to unit price, "
                "making growth costly to sustain."
            )

        # De-duplicate while preserving order.
        risk_tags_to_avoid = list(dict.fromkeys(risk_tags_to_avoid))

        narrative = (
            f"'{idea.name}' failed after {outcome.months_survived} month(s) "
            f"(outcome: {outcome.outcome}, final cash: {outcome.final_cash}). "
            + " ".join(primary_causes)
        )

        return RootCauseReport(
            idea_id=idea.id,
            idea_name=idea.name,
            outcome=outcome.outcome,
            primary_causes=primary_causes,
            risk_tags_to_avoid=risk_tags_to_avoid,
            narrative=narrative,
        )
