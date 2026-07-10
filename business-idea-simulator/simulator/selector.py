"""Generator-aware selection of the next business idea after a failure
(rule 5: select a brand-new business idea based on lessons learned).

Instead of filtering a fixed list, this samples a batch of candidate
archetype/niche/monetization combinations from the `IdeaGenerator`, scores
each by how much it carries the risk traits being avoided, and picks
randomly from the lowest-exposure third - same shape as the original
fixed-list selector, just generating candidates on the fly instead of
filtering them.
"""

import random
from typing import List, Set, Tuple

from .generator import IdeaGenerator
from .ideas import BusinessIdea

Combo = Tuple[str, str, str]


class IdeaSelector:
    def __init__(self, rng: random.Random, generator: IdeaGenerator, batch_size: int = 24):
        self.rng = rng
        self.generator = generator
        self.batch_size = batch_size
        self._next_idx = 0

    def _draw_idea(self, combo: Combo) -> BusinessIdea:
        archetype_id, niche_id, monetization_id = combo
        idea = self.generator.generate(
            archetype_id, niche_id, monetization_id, self.rng, self._next_idx
        )
        self._next_idx += 1
        return idea

    def select_next(
        self,
        tried_combos: Set[Combo],
        risk_tags_to_avoid: List[str],
    ) -> BusinessIdea:
        archetype_ids = self.generator.all_archetype_ids()
        niche_ids = self.generator.all_niche_ids()
        monetization_ids = self.generator.all_monetization_ids()
        total_combos = len(archetype_ids) * len(niche_ids) * len(monetization_ids)

        candidates: List[Tuple[Combo, BusinessIdea]] = []
        attempts = 0
        max_attempts = self.batch_size * 10
        while len(candidates) < self.batch_size and attempts < max_attempts:
            attempts += 1
            combo = (
                self.rng.choice(archetype_ids),
                self.rng.choice(niche_ids),
                self.rng.choice(monetization_ids),
            )
            if combo in tried_combos and len(tried_combos) < total_combos:
                continue
            candidates.append((combo, self._draw_idea(combo)))

        def penalty(idea: BusinessIdea) -> float:
            return sum(idea.risk_traits.get(tag, 0.0) for tag in risk_tags_to_avoid)

        candidates.sort(key=lambda c: penalty(c[1]))
        pool_size = max(1, len(candidates) // 3)
        combo, idea = self.rng.choice(candidates[:pool_size])
        tried_combos.add(combo)
        return idea
