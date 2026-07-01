from app.repositories.competition_repository import CompetitionRepository
import datetime

class CompetitionService:
    @staticmethod
    def get_active_competition():
        comp = CompetitionRepository.get_active()
        if not comp:
            # Self-healing fallback: Seed a default active competition
            now = datetime.datetime.utcnow()
            comp = CompetitionRepository.create(
                name="CTF Arena v2",
                description="Welcome to CTF Arena v2!",
                start_time=now,
                end_time=now + datetime.timedelta(days=7),
                registration_open=now - datetime.timedelta(days=1),
                registration_close=now + datetime.timedelta(days=7),
                is_active=True,
                allow_practice=True
            )
        return comp

    @staticmethod
    def create_competition(name, **kwargs):
        existing = CompetitionRepository.get_by_name(name)
        if existing:
            return None, "A competition with this name already exists."
        comp = CompetitionRepository.create(name=name, **kwargs)
        return comp, None

    @staticmethod
    def update_competition(comp_id, **kwargs):
        return CompetitionRepository.update(comp_id, **kwargs)

    @staticmethod
    def get_competition_state(comp):
        if not comp:
            return 'practice'
        if comp.is_archived:
            return 'archived'
        if comp.is_paused:
            return 'paused'
        if not comp.is_active:
            return 'draft'

        now = datetime.datetime.utcnow()
        
        # Check scheduling dates
        if comp.start_time and now < comp.start_time:
            if comp.registration_open and comp.registration_close and comp.registration_open <= now < comp.registration_close:
                return 'registration_open'
            return 'scheduled'
            
        if comp.end_time and now >= comp.end_time:
            return 'ended'
            
        if comp.freeze_time and comp.unfreeze_time and comp.freeze_time <= now < comp.unfreeze_time:
            return 'frozen'
            
        if comp.start_time and comp.end_time and comp.start_time <= now < comp.end_time:
            return 'running'

        return 'practice'

    @staticmethod
    def validate_state_transition(from_state, to_state):
        valid_transitions = {
            'draft': ['scheduled', 'running', 'practice'],
            'scheduled': ['registration_open', 'running', 'paused', 'draft'],
            'registration_open': ['running', 'paused', 'draft'],
            'running': ['frozen', 'paused', 'ended'],
            'paused': ['running', 'ended'],
            'frozen': ['running', 'unfrozen', 'ended'],
            'ended': ['archived'],
            'archived': [],
            'practice': ['draft', 'scheduled', 'running']
        }
        return to_state in valid_transitions.get(from_state, [])
