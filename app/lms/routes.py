import datetime
from flask import render_template, request, jsonify, redirect, url_for, g, flash
from flask_login import current_user
from app.lms import lms_bp
from app.utils.decorators import require_login
from app.extensions import db
from app.models.course import Course
from app.models.module import CourseModule
from app.models.lesson import Lesson
from app.models.course_enrollment import CourseEnrollment
from app.models.course_progress import CourseProgress
from app.models.learning_path import LearningPath, PathEnrollment
from app.models.badge import Badge
from app.models.skill import Skill, UserSkill
from app.models.certificate import Certificate
from app.models.career import Job, Employer, Resume
from app.models.submission import Submission

from app.services.certificate_service import CertificateService
from app.services.badge_service import BadgeService
from app.services.skill_service import SkillService
from app.services.mentor_service import MentorService
from app.services.career_service import CareerService

@lms_bp.route('/lms/dashboard', methods=['GET'])
@require_login
def dashboard():
    """LMS Student Dashboard."""
    # Seed databases just in case
    BadgeService.seed_badges()
    SkillService.seed_skills()

    enrollments = CourseEnrollment.query.filter_by(user_id=current_user.id).all()
    
    # Predefined learning paths
    paths = LearningPath.query.all()
    # If paths don't exist in DB, create from LEARNING_PATHS catalog
    if not paths:
        from app.models.learning_path import LEARNING_PATHS
        for slug, info in LEARNING_PATHS.items():
            lp = LearningPath(
                slug=slug,
                name=info['name'],
                description=info['description'],
                color=info['color'],
                required_skills=info['skills']
            )
            db.session.add(lp)
        db.session.commit()
        paths = LearningPath.query.all()

    path_enrollments = PathEnrollment.query.filter_by(user_id=current_user.id).all()
    user_badges = BadgeService.get_user_badges(current_user.id)
    user_skills = SkillService.get_user_skills(current_user.id)
    certs = CertificateService.get_user_certificates(current_user.id)
    resume = Resume.query.filter_by(user_id=current_user.id).first()

    return render_template(
        'dashboard_learning.html',
        enrollments=enrollments,
        paths=paths,
        path_enrollments={pe.path_id: pe for pe in path_enrollments},
        user_badges=user_badges,
        user_skills=user_skills,
        certs=certs,
        resume=resume
    )

@lms_bp.route('/lms/courses/<int:course_id>', methods=['GET'])
@require_login
def course_detail(course_id):
    """View course modules, lessons, and enrollment details."""
    course = Course.query.get_or_404(course_id)
    enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    
    return render_template(
        'course_detail.html',
        course=course,
        enrollment=enrollment
    )

@lms_bp.route('/lms/courses/<int:course_id>/enroll', methods=['POST'])
@require_login
def enroll_course(course_id):
    """Enroll a user in a course."""
    course = Course.query.get_or_404(course_id)
    existing = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if not existing:
        enr = CourseEnrollment(user_id=current_user.id, course_id=course.id, status='active')
        db.session.add(enr)
        db.session.flush()
        prog = CourseProgress(enrollment_id=enr.id, percentage=0.0, completed_lessons=[], completed_modules=[])
        db.session.add(prog)
        db.session.commit()
        flash('Enrolled in course successfully!', 'success')
    return redirect(url_for('lms.course_detail', course_id=course.id))

@lms_bp.route('/lms/lessons/<int:lesson_id>', methods=['GET'])
@require_login
def view_lesson(lesson_id):
    """View a single lesson and check lab completion status."""
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.module.course
    enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    
    # Check if this lesson has a lab / challenge required
    lab_solved = False
    if lesson.lab_required and lesson.challenge_id:
        # Check user solved submissions
        solved = Submission.query.filter_by(
            user_id=current_user.id,
            challenge_id=lesson.challenge_id,
            correct=True
        ).first()
        if solved:
            lab_solved = True

    completed = False
    if enrollment and enrollment.progress:
        completed = lesson.id in enrollment.progress.completed_lessons

    return render_template(
        'view_lesson.html',
        lesson=lesson,
        enrollment=enrollment,
        lab_solved=lab_solved,
        completed=completed
    )

@lms_bp.route('/lms/lessons/<int:lesson_id>/complete', methods=['POST'])
@require_login
def complete_lesson(lesson_id):
    """Mark a lesson as completed, update progress, and check for course completion/cert."""
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.module.course
    enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course.'}), 400

    # Lab requirement check
    if lesson.lab_required and lesson.challenge_id:
        solved = Submission.query.filter_by(
            user_id=current_user.id,
            challenge_id=lesson.challenge_id,
            correct=True
        ).first()
        if not solved:
            return jsonify({'error': 'You must solve the associated challenge lab first.'}), 400

    progress = enrollment.progress
    if not progress:
        progress = CourseProgress(enrollment_id=enrollment.id, percentage=0.0, completed_lessons=[], completed_modules=[])
        db.session.add(progress)

    progress.mark_lesson_complete(lesson.id)

    # Award skill XP for completing lesson
    skill_category = course.category
    SkillService.add_xp(current_user.id, skill_category, 25)

    # Recalculate percentage
    total = course.total_lessons
    if total > 0:
        progress.percentage = min(100.0, (len(progress.completed_lessons) / total) * 100.0)
    else:
        progress.percentage = 100.0

    # Auto issue certificate if 100% completed
    cert_issued = False
    if progress.percentage >= 100.0 and enrollment.status != 'completed':
        enrollment.status = 'completed'
        enrollment.completed_at = datetime.datetime.utcnow()
        
        # Issue Certificate
        CertificateService.issue(
            user_id=current_user.id,
            course_id=course.id,
            title=f"Certified: {course.title}",
            recipient_name=current_user.username,
            organization_id=getattr(g, 'current_org', None).id if getattr(g, 'current_org', None) else None
        )
        cert_issued = True
        # Award graduation badge
        BadgeService.award(current_user.id, 'course_graduate', reason=f"Graduated from {course.title}")

    db.session.commit()

    return jsonify({
        'success': True,
        'percentage': progress.percentage,
        'cert_issued': cert_issued
    }), 200

@lms_bp.route('/lms/mentor/chat', methods=['POST'])
@require_login
def mentor_chat():
    """Chat with the AI mentor about courses or lessons."""
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt')
    course_id = data.get('course_id')
    lesson_id = data.get('lesson_id')

    if not prompt:
        return jsonify({'error': 'Prompt is required.'}), 400

    response = MentorService.ask_mentor(
        user_id=current_user.id,
        prompt=prompt,
        course_id=course_id,
        lesson_id=lesson_id
    )

    return jsonify({'response': response}), 200

@lms_bp.route('/lms/paths/<int:path_id>/enroll', methods=['POST'])
@require_login
def enroll_path(path_id):
    """Enroll user in a Learning Path."""
    path = LearningPath.query.get_or_404(path_id)
    existing = PathEnrollment.query.filter_by(user_id=current_user.id, path_id=path.id).first()
    if not existing:
        pe = PathEnrollment(user_id=current_user.id, path_id=path.id, progress_pct=0.0, completed=False)
        db.session.add(pe)
        db.session.commit()
        flash(f'Enrolled in {path.name} path!', 'success')
    return redirect(url_for('lms.dashboard'))

@lms_bp.route('/verify/<string:verification_id>', methods=['GET'])
def verify_certificate(verification_id):
    """Public certificate verification page."""
    cert, error = CertificateService.verify(verification_id)
    return render_template('verify_certificate.html', cert=cert, error=error)

@lms_bp.route('/career/portal', methods=['GET'])
@require_login
def career_portal():
    """Career Portal displaying jobs and resume."""
    # Seed employer and jobs if none exist
    employers = Employer.query.all()
    if not employers:
        emp = CareerService.create_employer("SecureTech Corp", "https://securetech.io", "Leading security operations provider.")
        CareerService.verify_employer(emp.id)
        # Create a red team and blue team job
        CareerService.post_job(
            employer_id=emp.id,
            title="Junior SOC Analyst",
            description="Monitor logs, respond to incidents, work with security dashboards.",
            location="Remote",
            remote=True,
            required_skills=['incident_response', 'forensics'],
            required_badges=['100_points']
        )
        CareerService.post_job(
            employer_id=emp.id,
            title="Penetration Tester",
            description="Perform network and web application penetration tests.",
            location="On-site",
            remote=False,
            required_skills=['web_security', 'red_team'],
            required_badges=['500_points']
        )
    
    jobs = Job.query.filter_by(is_active=True).all()
    resume = Resume.query.filter_by(user_id=current_user.id).first()
    
    # Calculate eligibility for all jobs
    eligibility_map = {}
    for job in jobs:
        eligible, reason = CareerService.is_eligible_for_job(current_user.id, job.id)
        eligibility_map[job.id] = {'eligible': eligible, 'reason': reason}

    return render_template('career_portal.html', jobs=jobs, resume=resume, eligibility_map=eligibility_map)

@lms_bp.route('/career/resume', methods=['POST'])
@require_login
def update_resume():
    """Create or update user resume."""
    headline = request.form.get('headline')
    summary = request.form.get('summary')
    public = bool(request.form.get('public'))

    CareerService.update_resume(current_user.id, headline, summary, public)
    flash('Resume updated successfully!', 'success')
    return redirect(url_for('lms.career_portal'))


# LMS Administration Routes
from app.utils.decorators import require_admin

@lms_bp.route('/lms/admin/courses', methods=['GET'])
@require_admin
def admin_courses():
    courses = Course.query.all()
    certs = Certificate.query.all()
    employers = Employer.query.all()
    return render_template('admin_courses.html', courses=courses, certs=certs, employers=employers)

@lms_bp.route('/lms/admin/courses/create', methods=['POST'])
@require_admin
def admin_create_course():
    title = request.form.get('title')
    category = request.form.get('category')
    difficulty = request.form.get('difficulty')
    hours = float(request.form.get('estimated_hours', 1.0))
    
    course = Course(
        title=title,
        category=category,
        difficulty=difficulty,
        estimated_hours=hours,
        is_published=True,
        author_id=current_user.id
    )
    db.session.add(course)
    db.session.commit()
    flash(f'Course "{title}" created successfully!', 'success')
    return redirect(url_for('lms.admin_courses'))

@lms_bp.route('/lms/admin/courses/<int:course_id>/delete', methods=['POST'])
@require_admin
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully.', 'success')
    return redirect(url_for('lms.admin_courses'))

@lms_bp.route('/lms/admin/employers/<int:emp_id>/verify', methods=['POST'])
@require_admin
def admin_verify_employer(emp_id):
    CareerService.verify_employer(emp_id)
    flash('Employer verified successfully!', 'success')
    return redirect(url_for('lms.admin_courses'))

@lms_bp.route('/lms/admin/certificates/<int:cert_id>/revoke', methods=['POST'])
@require_admin
def admin_revoke_cert(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    CertificateService.revoke(cert, reason="Revoked by Administrator.")
    flash('Certificate revoked successfully.', 'success')
    return redirect(url_for('lms.admin_courses'))

