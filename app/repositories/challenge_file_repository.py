from app.extensions import db, safe_commit
from app.models.challenge_file import ChallengeFile

class ChallengeFileRepository:
    @staticmethod
    def get_by_id(file_id):
        return ChallengeFile.query.get(file_id)

    @staticmethod
    def get_for_challenge(challenge_id):
        return ChallengeFile.query.filter_by(challenge_id=challenge_id).all()

    @staticmethod
    def create(challenge_id, location, original_filename, stored_filename, size, checksum=None, mime_type=None):
        cf = ChallengeFile(
            challenge_id=challenge_id,
            location=location,
            original_filename=original_filename,
            stored_filename=stored_filename,
            size=size,
            checksum=checksum,
            mime_type=mime_type
        )
        db.session.add(cf)
        safe_commit()
        return cf

    @staticmethod
    def delete(file):
        db.session.delete(file)
        safe_commit()

    @staticmethod
    def increment_download(file):
        file.download_count += 1
        db.session.add(file)
        safe_commit()
        return file
