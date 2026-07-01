import os
import uuid
import hashlib
import mimetypes
from werkzeug.utils import secure_filename
from app.repositories.challenge_file_repository import ChallengeFileRepository

class FileService:
    @staticmethod
    def get_files_for_challenge(challenge_id):
        return ChallengeFileRepository.get_for_challenge(challenge_id)

    @staticmethod
    def get_file_by_id(file_id):
        return ChallengeFileRepository.get_by_id(file_id)

    @staticmethod
    def upload_file(challenge_id, file_obj, upload_folder):
        if not file_obj or file_obj.filename == '':
            return None, "No file selected."

        original_name = file_obj.filename
        safe_name = secure_filename(original_name)
        
        # Path traversal protection: extract basename
        safe_name = os.path.basename(safe_name)
        if not safe_name:
            # Fallback if secure_filename stripped everything
            safe_name = "uploaded_file_" + uuid.uuid4().hex[:8]

        # Prepend unique uuid prefix to prevent collision
        unique_prefix = uuid.uuid4().hex
        stored_name = f"{unique_prefix}_{safe_name}"
        
        # Ensure uploads folder exists
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, stored_name)

        # Save to disk
        file_obj.save(file_path)

        # Compute file statistics
        size = os.path.getsize(file_path)
        
        # Compute SHA-256 checksum
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        checksum = sha256.hexdigest()

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Stored location is relative path for URL downloads compatibility
        location = f"uploads/{stored_name}"

        # Create DB record
        cf = ChallengeFileRepository.create(
            challenge_id=challenge_id,
            location=location,
            original_filename=original_name,
            stored_filename=stored_name,
            size=size,
            checksum=checksum,
            mime_type=mime_type
        )
        return cf, None

    @staticmethod
    def delete_file(file_id, upload_folder):
        file_record = ChallengeFileRepository.get_by_id(file_id)
        if not file_record:
            return False, "File not found."

        # Delete from disk
        file_path = os.path.join(upload_folder, file_record.stored_filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                # Log error and continue to clean DB
                pass

        # Delete database entry
        ChallengeFileRepository.delete(file_record)
        return True, None

    @staticmethod
    def track_download(file_id):
        file_record = ChallengeFileRepository.get_by_id(file_id)
        if file_record:
            ChallengeFileRepository.increment_download(file_record)
            # Increment on the challenge as well
            if file_record.challenge:
                file_record.challenge.download_count += 1
                from app.extensions import db
                db.session.add(file_record.challenge)
                db.session.commit()
            return True
        return False
