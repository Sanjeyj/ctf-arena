import json
from app.extensions import db
from app.services.ai_service import AIService
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.skill import Skill

class MentorService:
    """AI Mentor service to guide students, answer course/lesson queries, and recommend paths."""

    @staticmethod
    def ask_mentor(user_id: int, prompt: str, course_id: int = None, lesson_id: int = None) -> str:
        """
        Send a prompt to the AI mentor with optional course/lesson context.
        Uses AIService for security sanitization and generation.
        """
        # Formulate system prompt / context
        context_parts = []
        if course_id:
            course = Course.query.get(course_id)
            if course:
                context_parts.append(f"Course: {course.title} (Category: {course.category}, Difficulty: {course.difficulty})")
        if lesson_id:
            lesson = Lesson.query.get(lesson_id)
            if lesson:
                context_parts.append(f"Lesson: {lesson.title}")
                if lesson.content_md:
                    context_parts.append(f"Lesson Content summary: {lesson.content_md[:200]}...")

        context_str = "\n".join(context_parts)
        full_prompt = (
            "You are an expert Cybersecurity Mentor. Guide the student on their learning journey.\n"
            f"Context:\n{context_str}\n\n"
            f"Student Question: {prompt}\n"
            "Provide a helpful, educational response without giving away flag values directly."
        )

        try:
            response_text, tokens, provider = AIService.generate(full_prompt)
            return response_text
        except ValueError as e:
            # Handle prompt injection or security sanitization error
            return f"Error: {str(e)}"
        except Exception as e:
            # Fallback mock/stub
            return f"I am your cybersecurity mentor. I am currently offline, but here is a tip: practice makes perfect! (Details: {str(e)})"

    @staticmethod
    def get_recommendations(user_id: int) -> list[dict]:
        """Get recommended courses/skills for the user."""
        # Simple recommendation engine based on current user skills
        from app.models.skill import UserSkill
        from app.models.course import Course

        user_skills = UserSkill.query.filter_by(user_id=user_id).all()
        # Find categories user has skills in, recommend courses of those categories
        categories = {us.skill.category for us in user_skills if us.skill}
        
        # If no skills yet, recommend general/beginner courses
        query = Course.query.filter_by(is_published=True)
        if categories:
            query = query.filter(Course.category.in_(list(categories)))
        
        recommended_courses = query.order_by(Course.difficulty.asc()).limit(3).all()
        return [
            {
                'id': c.id,
                'title': c.title,
                'category': c.category,
                'difficulty': c.difficulty,
                'estimated_hours': c.estimated_hours
            } for c in recommended_courses
        ]
