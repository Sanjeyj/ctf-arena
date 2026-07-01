import os
import uuid
import hashlib
import mimetypes
from werkzeug.utils import secure_filename
from app.repositories.challenge_file_repository import ChallengeFileRepository
from app.extensions import db, safe_commit

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
        name_lower = original_name.lower()

        # Enforce allowed extensions list
        from flask import current_app
        allowed_exts = current_app.config.get("ALLOWED_EXTENSIONS", {
            'zip', 'tar.gz', 'tgz', 'tar', 'gz', 'txt', 'json', 
            'png', 'jpg', 'jpeg', 'gif', 'bmp', 'pdf', 'mp3', 
            'mp4', 'wav', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 
            'pptx', 'csv', 'xml', 'yaml', 'yml', 'md'
        })
        blocked_exts = {'py', 'sh', 'php', 'exe', 'html', 'htm', 'js', 'jsp', 'asp', 'aspx', 'bat', 'cmd', 'pl', 'cgi', 'msi', 'jar', 'vbs'}
        
        has_allowed_ext = False
        for ext in ['tar.gz', 'tar.bz2', 'tar.xz']:
            if name_lower.endswith('.' + ext):
                has_allowed_ext = True
                break
        if not has_allowed_ext:
            ext = name_lower.rsplit('.', 1)[-1] if '.' in name_lower else ''
            if ext in allowed_exts:
                has_allowed_ext = True

        if not has_allowed_ext:
            return None, "File extension not allowed."

        # Explicitly block execution-prone/script extensions
        actual_ext = name_lower.rsplit('.', 1)[-1] if '.' in name_lower else ''
        if actual_ext in blocked_exts:
            return None, "Executable or script files are rejected."
        for ext in blocked_exts:
            if f'.{ext}.' in name_lower or name_lower.endswith(f'.{ext}'):
                return None, "Executable or script files are rejected."

        # Verify MIME type
        content_type = file_obj.content_type
        guessed_mime, _ = mimetypes.guess_type(original_name)
        blocked_mimes = {
            'text/html', 'text/javascript', 'application/javascript', 'application/x-javascript',
            'application/x-sh', 'application/x-shellscript', 'text/x-python', 'application/x-python-code',
            'application/x-msdownload', 'application/x-dsexec', 'application/x-executable',
            'application/x-sharedlib', 'application/octet-stream-executable', 'text/x-php', 'application/x-httpd-php'
        }
        if content_type in blocked_mimes or guessed_mime in blocked_mimes:
            return None, "Executable or script files are rejected."

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
                db.session.add(file_record.challenge)
                safe_commit()
            return True
        return False
