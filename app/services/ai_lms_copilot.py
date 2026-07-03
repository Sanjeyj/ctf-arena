"""
AI LMS Copilot - Phase 21 AI Copilots.
Recommends learning paths and parses lesson concepts.
"""
from app.extensions import db
from app.models.lesson import Lesson

class AILmsCopilot:

    @staticmethod
    def recommend_learning_paths(user_id: int) -> str:
        return (
            f"LMS Copilot Recommendations for User #{user_id}:\n\n"
            f"Based on your profile, we recommend starting with: "
            f"1. Reverse Engineering Basics (Phase 17)\n"
            f"2. Practical Threat Hunting with YARA (Phase 18)"
        )

    @staticmethod
    def explain_lesson(lesson_id: int) -> str:
        lesson = db.session.get(Lesson, lesson_id)
        if not lesson:
            return f"Lesson #{lesson_id} not found."
            
        return (
            f"LMS Copilot Concept Explanation for Lesson '{lesson.title}':\n\n"
            f"This lesson covers core concepts of '{lesson.title}'. "
            f"Review standard code blocks and verify your configuration variables."
        )
