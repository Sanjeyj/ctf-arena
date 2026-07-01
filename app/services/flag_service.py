import re
import hashlib
from app.repositories.flag_repository import FlagRepository

class FlagService:
    @staticmethod
    def get_flags_for_challenge(challenge_id):
        return FlagRepository.get_for_challenge(challenge_id)

    @staticmethod
    def get_flag_by_id(flag_id):
        return FlagRepository.get_by_id(flag_id)

    @staticmethod
    def create_flag(challenge_id, content, flag_type="exact", is_case_sensitive=True, priority=0, notes=None, enabled=True):
        content = content.strip()
        if not content:
            return None, "Flag content cannot be empty."
        flag = FlagRepository.create(challenge_id, content, flag_type, is_case_sensitive, priority, notes, enabled)
        return flag, None

    @staticmethod
    def update_flag(flag_id, **kwargs):
        flag = FlagRepository.get_by_id(flag_id)
        if not flag:
            return None, "Flag not found."
        if "content" in kwargs and not kwargs["content"].strip():
            return None, "Flag content cannot be empty."
        updated = FlagRepository.update(flag, **kwargs)
        return updated, None

    @staticmethod
    def delete_flag(flag_id):
        flag = FlagRepository.get_by_id(flag_id)
        if not flag:
            return False, "Flag not found."
        FlagRepository.delete(flag)
        return True, None

    @staticmethod
    def verify_flag(flag, user_input):
        if not flag.enabled:
            return False
            
        flag_content = flag.content.strip()
        user_input = user_input.strip()
        
        # Determine case sensitivity
        if not flag.is_case_sensitive:
            flag_content = flag_content.lower()
            user_input = user_input.lower()

        # Match type evaluation
        if flag.flag_type == "exact":
            return flag_content == user_input
            
        elif flag.flag_type == "regex":
            try:
                flags = re.IGNORECASE if not flag.is_case_sensitive else 0
                pattern = re.compile(flag.content.strip(), flags)
                return bool(pattern.match(user_input))
            except Exception:
                return False
                
        elif flag.flag_type == "hashed":
            # Compare sha256 of user input with stored flag content hash
            hashed_input = hashlib.sha256(user_input.encode('utf-8')).hexdigest()
            return flag_content == hashed_input
            
        return False
