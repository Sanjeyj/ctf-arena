import csv
import io
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.challenge_repository import ChallengeRepository
from app.services.flag_service import FlagService

class SubmissionService:
    @staticmethod
    def get_submissions(page=1, per_page=50, user_id=None, challenge_id=None,
                        status=None, correct=None, order_by="time_desc"):
        items, total = SubmissionRepository.get_all(
            page=page, per_page=per_page,
            user_id=user_id, challenge_id=challenge_id,
            status=status, correct=correct, order_by=order_by
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    @staticmethod
    def rejudge(sub_id):
        """Re-evaluate a submission against current challenge flags."""
        sub = SubmissionRepository.get_by_id(sub_id)
        if not sub:
            return False, "Submission not found."
        if not sub.submitted_flag:
            return False, "No flag text recorded for this submission; cannot rejudge."

        ch = ChallengeRepository.get_by_id(sub.challenge_id)
        if not ch:
            return False, "Challenge not found."

        # Evaluate against all active flags
        correct = any(FlagService.verify_flag(f, sub.submitted_flag) for f in ch.flags if f.enabled)

        if correct:
            new_points = ch.current_points
            SubmissionRepository.update_status(sub.id, correct=True, status="correct", points=new_points)
            return True, f"Rejudged: Correct — {new_points} pts awarded."
        else:
            SubmissionRepository.update_status(sub.id, correct=False, status="wrong", points=0)
            return True, "Rejudged: Incorrect."

    @staticmethod
    def mark_correct(sub_id):
        sub = SubmissionRepository.get_by_id(sub_id)
        if not sub:
            return False, "Submission not found."
        ch = ChallengeRepository.get_by_id(sub.challenge_id)
        pts = ch.current_points if ch else sub.points
        SubmissionRepository.update_status(sub.id, correct=True, status="correct", points=pts)
        return True, "Submission marked correct."

    @staticmethod
    def mark_incorrect(sub_id):
        sub = SubmissionRepository.get_by_id(sub_id)
        if not sub:
            return False, "Submission not found."
        SubmissionRepository.update_status(sub.id, correct=False, status="wrong", points=0)
        return True, "Submission marked incorrect."

    @staticmethod
    def delete(sub_id):
        return SubmissionRepository.delete(sub_id)

    @staticmethod
    def export_csv():
        """Export all submissions as a CSV string."""
        subs, _ = SubmissionRepository.get_all(page=1, per_page=100000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "user_id", "challenge_id", "points", "correct", "status",
                         "submitted_flag", "time", "elapsed"])
        for sub in subs:
            writer.writerow([
                sub.id, sub.user_id, sub.challenge_id,
                sub.points, sub.correct, sub.status,
                sub.submitted_flag or "",
                sub.time.isoformat() if sub.time else "",
                sub.elapsed or 0
            ])
        return output.getvalue()
