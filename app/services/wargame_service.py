"""
WargameService - Phase 29 Global Cyber Command Center.
Simulates strategic war-game scenarios, scores outcomes, and generates summaries.
"""
import random
from app.extensions import db
from app.models.war_game import WarGame


class WargameService:
    @staticmethod
    def simulate(game_id: int) -> dict:
        """Run a war-game simulation and randomly determine the result."""
        game = db.session.get(WarGame, game_id)
        if not game:
            return {'error': 'War game not found'}
        outcomes = ['blue_win', 'red_win', 'draw']
        game.result = random.choice(outcomes)
        game.score = round(random.uniform(0.3, 1.0), 2)
        db.session.commit()
        return {
            'game_id': game_id,
            'scenario': game.scenario,
            'result': game.result,
            'score': game.score,
            'simulation': 'complete',
        }

    @staticmethod
    def score(game_id: int) -> float:
        """Return the score for a given war game."""
        game = db.session.get(WarGame, game_id)
        if not game:
            return 0.0
        return game.score

    @staticmethod
    def summarize(org_id: int) -> dict:
        """Summarize all war-game outcomes for an organization."""
        games = WarGame.query.filter_by(organization_id=org_id).all()
        if not games:
            return {'total': 0, 'blue_wins': 0, 'red_wins': 0, 'draws': 0, 'avg_score': 0.0}
        blue = sum(1 for g in games if g.result == 'blue_win')
        red = sum(1 for g in games if g.result == 'red_win')
        draw = sum(1 for g in games if g.result == 'draw')
        avg = round(sum(g.score for g in games) / len(games), 3)
        return {
            'total': len(games),
            'blue_wins': blue,
            'red_wins': red,
            'draws': draw,
            'avg_score': avg,
        }
