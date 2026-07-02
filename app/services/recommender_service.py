"""
RecommenderService — Collaborative-filtering challenge recommender.

Algorithm:
  1. Find users who solved at least one of the same challenges as the target user.
  2. Collect challenges those similar users solved that the target has NOT solved.
  3. Score by frequency (popularity among similar users), weighted by:
     - category affinity (matching categories get +0.3 bonus)
     - difficulty progression (one step harder than max solved difficulty gets +0.5)
  4. Return top-N by score, excluding hidden and archived challenges.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_DIFFICULTY_ORDER = ['Easy', 'Medium', 'Hard', 'Insane']


def _difficulty_index(label: str) -> int:
    try:
        return _DIFFICULTY_ORDER.index(label.capitalize())
    except ValueError:
        return 1  # default Medium


class RecommenderService:

    @staticmethod
    def _get_solved_ids(user_id: int) -> set[int]:
        try:
            from app.models.submission import Submission
            rows = Submission.query.filter_by(user_id=user_id, correct=True).all()
            return {r.challenge_id for r in rows}
        except Exception:
            return set()

    @staticmethod
    def _get_user_categories(solved_ids: set[int]) -> dict[Optional[int], int]:
        """Map category_id → count of solved challenges in that category."""
        if not solved_ids:
            return {}
        try:
            from app.models.challenge import Challenge
            challenges = Challenge.query.filter(Challenge.id.in_(solved_ids)).all()
            counts: dict[Optional[int], int] = {}
            for ch in challenges:
                counts[ch.category_id] = counts.get(ch.category_id, 0) + 1
            return counts
        except Exception:
            return {}

    @staticmethod
    def _get_max_solved_difficulty(solved_ids: set[int]) -> int:
        if not solved_ids:
            return 0
        try:
            from app.models.challenge import Challenge
            challenges = Challenge.query.filter(Challenge.id.in_(solved_ids)).all()
            indices = [_difficulty_index(ch.difficulty or 'Easy') for ch in challenges]
            return max(indices) if indices else 0
        except Exception:
            return 0

    @staticmethod
    def _find_similar_users(solved_ids: set[int], user_id: int) -> set[int]:
        if not solved_ids:
            return set()
        try:
            from app.models.submission import Submission
            rows = (
                Submission.query
                .filter(
                    Submission.challenge_id.in_(solved_ids),
                    Submission.user_id != user_id,
                    Submission.correct == True,
                )
                .all()
            )
            return {r.user_id for r in rows}
        except Exception:
            return set()

    @staticmethod
    def recommend(user, limit: int = 5) -> list[dict]:
        """
        Return top-N recommended challenges for the given user.

        Each result dict contains: id, title, category_id, difficulty, score.
        """
        from app.models.challenge import Challenge
        from app.models.submission import Submission
        from app.extensions import db

        user_id = user.id
        solved_ids = RecommenderService._get_solved_ids(user_id)
        cat_affinity = RecommenderService._get_user_categories(solved_ids)
        max_diff_idx = RecommenderService._get_max_solved_difficulty(solved_ids)
        similar_users = RecommenderService._find_similar_users(solved_ids, user_id)

        if not similar_users:
            # Cold-start: return beginner-friendly unsolved visible challenges
            try:
                cold = (
                    Challenge.query
                    .filter(
                        Challenge.visible == True,
                        Challenge.archived == False,
                        ~Challenge.id.in_(solved_ids or {0}),
                    )
                    .order_by(Challenge.solve_count.desc())
                    .limit(limit)
                    .all()
                )
                return [
                    {
                        'id': ch.id,
                        'title': ch.title,
                        'category_id': ch.category_id,
                        'difficulty': ch.difficulty,
                        'score': 0.5,
                        'reason': 'Popular unsolved challenge',
                    }
                    for ch in cold
                ]
            except Exception:
                return []

        # Collect candidates from similar users
        try:
            candidate_rows = (
                Submission.query
                .filter(
                    Submission.user_id.in_(similar_users),
                    Submission.correct == True,
                    ~Submission.challenge_id.in_(solved_ids or {0}),
                )
                .all()
            )
        except Exception:
            return []

        # Score candidates
        scores: dict[int, float] = {}
        for row in candidate_rows:
            scores[row.challenge_id] = scores.get(row.challenge_id, 0.0) + 1.0

        if not scores:
            return []

        # Load challenge objects for bonus scoring
        try:
            cands = Challenge.query.filter(
                Challenge.id.in_(scores.keys()),
                Challenge.visible == True,
                Challenge.archived == False,
            ).all()
        except Exception:
            return []

        results = []
        for ch in cands:
            base_score = scores.get(ch.id, 0.0)

            # Category affinity bonus
            if cat_affinity.get(ch.category_id, 0) > 0:
                base_score += 0.3

            # Difficulty progression bonus (one step harder than max solved)
            diff_idx = _difficulty_index(ch.difficulty or 'Easy')
            if diff_idx == max_diff_idx + 1:
                base_score += 0.5
            elif diff_idx > max_diff_idx + 2:
                base_score *= 0.5  # too far ahead — penalise

            results.append({
                'id': ch.id,
                'title': ch.title,
                'category_id': ch.category_id,
                'difficulty': ch.difficulty,
                'score': round(base_score, 3),
                'reason': 'Solved by similar users',
            })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
