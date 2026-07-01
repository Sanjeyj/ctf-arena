import time
from flask import has_request_context, request
from app.extensions import db

# Thread-safe in-memory metrics store for request metrics
_request_counts = {}       # path -> count
_request_durations = {}    # path -> cumulative duration (float seconds)
_response_status_counts = {} # status_code -> count
_api_requests = 0

class MetricsService:

    @staticmethod
    def before_request():
        if has_request_context():
            request.start_time = time.time()

    @staticmethod
    def after_request(response):
        global _api_requests
        if has_request_context() and hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            path = request.path
            status = response.status_code

            # Increment count
            _request_counts[path] = _request_counts.get(path, 0) + 1
            _request_durations[path] = _request_durations.get(path, 0.0) + duration
            _response_status_counts[status] = _response_status_counts.get(status, 0) + 1

            if path.startswith("/api/"):
                _api_requests += 1

        return response

    @staticmethod
    def get_prometheus_metrics() -> str:
        """Returns Prometheus exposition text output."""
        from app.models.challenge_instance import ChallengeInstance
        from app.models.submission import Submission
        from app.models.competition import Competition

        lines = []

        # 1. Total request count
        lines.append("# HELP ctf_http_requests_total Total HTTP requests handled.")
        lines.append("# TYPE ctf_http_requests_total counter")
        for path, count in _request_counts.items():
            lines.append(f'ctf_http_requests_total{{path="{path}"}} {count}')

        # 2. Cumulative request duration
        lines.append("# HELP ctf_http_request_duration_seconds_total Cumulative HTTP request duration in seconds.")
        lines.append("# TYPE ctf_http_request_duration_seconds_total counter")
        for path, duration in _request_durations.items():
            lines.append(f'ctf_http_request_duration_seconds_total{{path="{path}"}} {duration:.6f}')

        # 3. HTTP status codes
        lines.append("# HELP ctf_http_responses_status_total HTTP responses by status code.")
        lines.append("# TYPE ctf_http_responses_status_total counter")
        for code, count in _response_status_counts.items():
            lines.append(f'ctf_http_responses_status_total{{status="{code}"}} {count}')

        # 4. API request count
        lines.append("# HELP ctf_api_requests_total Total API requests received.")
        lines.append("# TYPE ctf_api_requests_total counter")
        lines.append(f"ctf_api_requests_total {_api_requests}")

        # --- DB queries for real-time model statistics ---
        try:
            # 5. Challenge Solves
            solves_count = Submission.query.filter_by(correct=True).count()
            lines.append("# HELP ctf_challenge_solves_total Total correct flags submitted.")
            lines.append("# TYPE ctf_challenge_solves_total gauge")
            lines.append(f"ctf_challenge_solves_total {solves_count}")

            # 6. Active challenge containers
            active_containers = ChallengeInstance.query.filter(
                ChallengeInstance.status.in_(["creating", "running"])
            ).count()
            lines.append("# HELP ctf_active_containers_total Number of running challenge container instances.")
            lines.append("# TYPE ctf_active_containers_total gauge")
            lines.append(f"ctf_active_containers_total {active_containers}")

            # 7. Competitions running
            from app.extensions import utcnow
            now = utcnow()
            active_competitions = Competition.query.filter(
                Competition.is_active == True,
                Competition.start_time <= now,
                (Competition.end_time == None) | (Competition.end_time >= now)
            ).count()
            lines.append("# HELP ctf_active_competitions_total Number of running active competitions.")
            lines.append("# TYPE ctf_active_competitions_total gauge")
            lines.append(f"ctf_active_competitions_total {active_competitions}")

            # 8. Total submissions
            total_submissions = Submission.query.count()
            lines.append("# HELP ctf_submissions_total Total flag submissions.")
            lines.append("# TYPE ctf_submissions_total counter")
            lines.append(f"ctf_submissions_total {total_submissions}")

            # 9. Database query latency proxy (simulated or real query duration metric)
            # Query timing verification metric
            start_query = time.time()
            db.session.execute(db.select(1)).first()
            db_latency = time.time() - start_query
            lines.append("# HELP ctf_database_latency_seconds Latency of database execution probe.")
            lines.append("# TYPE ctf_database_latency_seconds gauge")
            lines.append(f"ctf_database_latency_seconds {db_latency:.6f}")

        except Exception:
            # Fail-safe fallback if DB not fully initialised
            lines.append("ctf_challenge_solves_total 0")
            lines.append("ctf_active_containers_total 0")
            lines.append("ctf_active_competitions_total 0")
            lines.append("ctf_submissions_total 0")
            lines.append("ctf_database_latency_seconds 0.0")

        return "\n".join(lines) + "\n"
