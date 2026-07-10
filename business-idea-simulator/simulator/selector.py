"""Rule-based selection of the next business idea after a failure
(rule 5: select a brand-new business idea based on lessons learned).
"""

import random
from typing import List

from .ideas import BusinessIdea


class IdeaSelector:
    def __init__(self, rng: random.Random):
        self.rng = rng

    def select_next(
        self,
        idea_bank: List[BusinessIdea],
        tried_ids: List[str],
        risk_tags_to_avoid: List[str],
    ) -> BusinessIdea:
        candidates = [idea for idea in idea_bank if idea.id not in tried_ids]
        if not candidates:
            # Idea bank exhausted - allow repeats rather than stalling the loop.
            candidates = list(idea_bank)

        def penalty(idea: BusinessIdea) -> float:
            return sum(idea.risk_traits.get(tag, 0.0) for tag in risk_tags_to_avoid)

        candidates.sort(key=penalty)
        pool_size = max(1, len(candidates) // 3)
        return self.rng.choice(candidates[:pool_size])
