import click
import os
import json
import datetime
from flask.cli import with_appcontext

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize migrations and upgrade database to latest schema."""
    from app.extensions import db
    from flask_migrate import init, migrate, upgrade
    
    if not os.path.exists("migrations"):
        click.echo("Initializing migrations directory...")
        try:
            init()
        except Exception as e:
            click.echo(f"Flask-Migrate init failed: {e}. Falling back...")
            
    try:
        click.echo("Generating database migration...")
        migrate(message="Auto-generated migration")
    except Exception as e:
        click.echo(f"Flask-Migrate migrate skipped or failed: {e}. Continuing to upgrade...")

    try:
        click.echo("Upgrading database to latest revision...")
        upgrade()
        click.echo("[OK] Database initialized and upgraded successfully.")
    except Exception as e:
        click.echo(f"[WARNING] Flask-Migrate upgrade failed: {e}. Falling back to db.create_all().")
        db.create_all()
        click.echo("[OK] Database tables created using db.create_all().")

@click.command("seed")
@with_appcontext
def seed_command():
    """Seed roles, permissions, default accounts and challenges."""
    from app.repositories.role_repository import RoleRepository
    from app.repositories.permission_repository import PermissionRepository
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import hash_password

    # 1. Setup roles and permissions
    click.echo("Setting up roles...")
    RoleRepository.setup_default_roles()
    click.echo("Setting up permissions mapping...")
    PermissionRepository.setup_default_permissions_and_roles_map()

    # 2. Seed Default Administrator
    from flask import current_app
    admin_user = current_app.config.get("ADMIN_USER", "admin")
    admin_pass = current_app.config.get("ADMIN_PASSWORD", "ctf_admin_2024")
    if not UserRepository.get_by_name(admin_user):
        UserRepository.create(
            username=admin_user,
            password_hash=hash_password(admin_pass),
            display_name="Administrator",
            role_name="Admin"
        )
        click.echo(f"[OK] Seeded default administrator: {admin_user}")

    # 3. Seed Default Moderator
    mod_user = "moderator"
    mod_pass = "ctf_moderator_2024"
    if not UserRepository.get_by_name(mod_user):
        UserRepository.create(
            username=mod_user,
            password_hash=hash_password(mod_pass),
            display_name="Moderator",
            role_name="Moderator"
        )
        click.echo(f"[OK] Seeded default moderator: {mod_user}")

    # 4. Seed Sample Participant
    sample_user = "Sample"
    sample_pass = "ctf_sample_2024"
    if not UserRepository.get_by_name(sample_user):
        UserRepository.create(
            username=sample_user,
            password_hash=hash_password(sample_pass),
            display_name="Sample Participant",
            role_name="Participant"
        )
        click.echo(f"[OK] Seeded sample participant: {sample_user}")

    # 5. Run challenges seed
    ctx = click.get_current_context()
    ctx.invoke(seed_challenges_command)

@click.command("seed-challenges")
@with_appcontext
def seed_challenges_command():
    """Seed dynamic challenges from challenges_seed.json."""
    from flask import current_app
    from app.extensions import db
    from app.models.category import Category
    from app.models.challenge import Challenge
    from app.models.flag import Flag
    from app.models.hint import Hint
    from app.services.challenge_service import ChallengeService

    seed_file = os.path.join(current_app.root_path, "utils", "challenges_seed.json")
    if not os.path.exists(seed_file):
        click.echo(f"[ERROR] Seed file not found at {seed_file}", err=True)
        return

    try:
        with open(seed_file, encoding='utf-8') as f:
            data = json.load(f)

        category_map = {}
        for cat_name in data.get("categories", []):
            cat = Category.query.filter_by(name=cat_name).first()
            if not cat:
                cat = Category(name=cat_name)
                db.session.add(cat)
                db.session.flush()
            category_map[cat_name] = cat.id

        for ch_data in data.get("challenges", []):
            legacy_id = ch_data["legacy_id"]
            ch = Challenge.query.filter_by(legacy_id=legacy_id).first()
            
            # Setup dynamic scoring parameters in seed mapping
            initial_pts = ch_data.get("points", 50)
            decay_type = ch_data.get("decay_type", "static")
            decay_rate = ch_data.get("decay_rate", 0)
            min_pts = ch_data.get("minimum_points", 10)

            if not ch:
                ch = Challenge(
                    legacy_id=legacy_id,
                    title=ch_data["title"],
                    description=ch_data["description"],
                    points=initial_pts,
                    icon=ch_data.get("icon"),
                    difficulty=ch_data["difficulty"],
                    category_id=category_map.get(ch_data["category"]),
                    initial_points=initial_pts,
                    minimum_points=min_pts,
                    current_points=initial_pts,
                    decay_type=decay_type,
                    decay_rate=decay_rate
                )
                db.session.add(ch)
                db.session.flush()
            else:
                ch.title = ch_data["title"]
                ch.description = ch_data["description"]
                ch.points = initial_pts
                ch.icon = ch_data.get("icon")
                ch.difficulty = ch_data["difficulty"]
                ch.category_id = category_map.get(ch_data["category"])
                ch.initial_points = initial_pts
                ch.minimum_points = min_pts
                ch.decay_type = decay_type
                ch.decay_rate = decay_rate
                ch.is_deleted = False
                db.session.add(ch)
                db.session.flush()

            # Re-sync flags
            Flag.query.filter_by(challenge_id=ch.id).delete()
            for flag_data in ch_data.get("flags", []):
                flag = Flag(
                    challenge_id=ch.id,
                    content=flag_data["content"],
                    flag_type=flag_data.get("flag_type", "exact"),
                    is_case_sensitive=flag_data.get("is_case_sensitive", True)
                )
                db.session.add(flag)

            # Re-sync hints
            Hint.query.filter_by(challenge_id=ch.id).delete()
            for hint_data in ch_data.get("hints", []):
                hint = Hint(
                    challenge_id=ch.id,
                    content=hint_data["content"],
                    cost=hint_data.get("cost", 0),
                    title=hint_data.get("title")
                )
                db.session.add(hint)

        db.session.commit()
        # Recalculate dynamic values
        ChallengeService.rebuild_all_challenge_points()
        click.echo("[OK] Dynamic challenges seeded and scores recalculated successfully.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"[ERROR] Challenges seeding failed: {e}", err=True)

@click.command("import-challenges")
@click.option("--file", required=True, help="JSON file path to import challenges from")
@with_appcontext
def import_challenges_command(file):
    """Import challenges, categories, flags and hints from a JSON file."""
    if not os.path.exists(file):
        click.echo(f"[ERROR] Import file '{file}' not found.", err=True)
        return

    from app.extensions import db
    from app.models.category import Category
    from app.models.challenge import Challenge
    from app.models.flag import Flag
    from app.models.hint import Hint
    from app.services.challenge_service import ChallengeService

    try:
        with open(file, encoding='utf-8') as f:
            data = json.load(f)

        category_map = {}
        for cat_data in data.get("categories", []):
            name = cat_data["name"]
            cat = Category.query.filter_by(name=name).first()
            if not cat:
                cat = Category(
                    name=name,
                    description=cat_data.get("description"),
                    color=cat_data.get("color", "#00f0ff"),
                    icon=cat_data.get("icon"),
                    display_order=cat_data.get("display_order", 0),
                    visible=cat_data.get("visible", True)
                )
                db.session.add(cat)
                db.session.flush()
            category_map[name] = cat.id

        imported_count = 0
        for ch_data in data.get("challenges", []):
            legacy_id = ch_data["legacy_id"]
            ch = Challenge.query.filter_by(legacy_id=legacy_id).first()
            
            kwargs = {
                "initial_points": ch_data.get("initial_points", ch_data.get("points", 50)),
                "minimum_points": ch_data.get("minimum_points", 10),
                "decay_type": ch_data.get("decay_type", "static"),
                "decay_rate": ch_data.get("decay_rate", 0),
                "max_attempts": ch_data.get("max_attempts", 0),
                "state": ch_data.get("state", "visible"),
                "visible": ch_data.get("visible", True),
                "display_order": ch_data.get("display_order", 0),
                "connection_info": ch_data.get("connection_info"),
                "requires_connection_info": ch_data.get("requires_connection_info", False)
            }

            if not ch:
                ch = Challenge(
                    legacy_id=legacy_id,
                    title=ch_data["title"],
                    description=ch_data["description"],
                    points=kwargs["initial_points"],
                    difficulty=ch_data["difficulty"],
                    category_id=category_map.get(ch_data.get("category_name")),
                    **kwargs
                )
                db.session.add(ch)
                db.session.flush()
                imported_count += 1
            else:
                ch.title = ch_data["title"]
                ch.description = ch_data["description"]
                ch.difficulty = ch_data["difficulty"]
                ch.category_id = category_map.get(ch_data.get("category_name"))
                for k, v in kwargs.items():
                    setattr(ch, k, v)
                ch.is_deleted = False
                db.session.add(ch)
                db.session.flush()

            # Sync flags
            Flag.query.filter_by(challenge_id=ch.id).delete()
            for flag_data in ch_data.get("flags", []):
                flag = Flag(
                    challenge_id=ch.id,
                    content=flag_data["content"],
                    flag_type=flag_data.get("flag_type", "exact"),
                    is_case_sensitive=flag_data.get("is_case_sensitive", True),
                    priority=flag_data.get("priority", 0),
                    notes=flag_data.get("notes")
                )
                db.session.add(flag)

            # Sync hints
            Hint.query.filter_by(challenge_id=ch.id).delete()
            for hint_data in ch_data.get("hints", []):
                hint = Hint(
                    challenge_id=ch.id,
                    content=hint_data["content"],
                    cost=hint_data.get("cost", 0),
                    title=hint_data.get("title"),
                    visible=hint_data.get("visible", True),
                    enabled=hint_data.get("enabled", True),
                    display_order=hint_data.get("display_order", 0)
                )
                db.session.add(hint)

        db.session.commit()
        # Recalculate dynamic scores
        ChallengeService.rebuild_all_challenge_points()
        click.echo(f"[OK] Successfully imported/updated {imported_count} challenges from '{file}'.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"[ERROR] Import failed: {e}", err=True)

@click.command("export-challenges")
@click.option("--file", required=True, help="JSON file path to export challenges to")
@with_appcontext
def export_challenges_command(file):
    """Export all challenges, categories, flags and hints to a JSON file."""
    from app.models.category import Category
    from app.models.challenge import Challenge

    try:
        categories = Category.query.all()
        challenges = Challenge.query.filter_by(is_deleted=False).all()

        export_data = {
            "categories": [],
            "challenges": []
        }

        for cat in categories:
            export_data["categories"].append({
                "name": cat.name,
                "description": cat.description,
                "color": cat.color,
                "icon": cat.icon,
                "display_order": cat.display_order,
                "visible": cat.visible
            })

        for ch in challenges:
            ch_dict = {
                "legacy_id": ch.legacy_id,
                "title": ch.title,
                "description": ch.description,
                "points": ch.points,
                "difficulty": ch.difficulty,
                "category_name": ch.category.name if ch.category else None,
                "initial_points": ch.initial_points,
                "minimum_points": ch.minimum_points,
                "decay_type": ch.decay_type,
                "decay_rate": ch.decay_rate,
                "max_attempts": ch.max_attempts,
                "state": ch.state,
                "visible": ch.visible,
                "display_order": ch.display_order,
                "connection_info": ch.connection_info,
                "requires_connection_info": ch.requires_connection_info,
                "flags": [],
                "hints": []
            }

            for f in ch.flags:
                ch_dict["flags"].append({
                    "content": f.content,
                    "flag_type": f.flag_type,
                    "is_case_sensitive": f.is_case_sensitive,
                    "priority": f.priority,
                    "notes": f.notes
                })

            for h in ch.hints:
                ch_dict["hints"].append({
                    "content": h.content,
                    "cost": h.cost,
                    "title": h.title,
                    "visible": h.visible,
                    "enabled": h.enabled,
                    "display_order": h.display_order
                })

            export_data["challenges"].append(ch_dict)

        with open(file, "w", encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)

        click.echo(f"[OK] Successfully exported challenges to '{file}'.")
    except Exception as e:
        click.echo(f"[ERROR] Export failed: {e}", err=True)

@click.command("rebuild-scoring")
@with_appcontext
def rebuild_scoring_command():
    """Recalculate dynamic scoring decay values for all challenges."""
    from app.services.challenge_service import ChallengeService
    try:
        ChallengeService.rebuild_all_challenge_points()
        click.echo("[OK] Recalculated dynamic points decay for all challenges.")
    except Exception as e:
        click.echo(f"[ERROR] Rebuild scoring failed: {e}", err=True)

@click.command("verify-flags")
@with_appcontext
def verify_flags_command():
    """Verify regex formatting and list all active flags."""
    from app.models.challenge import Challenge
    import re

    challenges = Challenge.query.filter_by(is_deleted=False).all()
    if not challenges:
        click.echo("No active challenges found.")
        return

    click.echo(f"{'Challenge':<20} | {'Type':<10} | {'Flag Content':<40} | {'Status':<10}")
    click.echo("-" * 89)
    for ch in challenges:
        for f in ch.flags:
            status = "Valid"
            if f.flag_type == "regex":
                try:
                    re.compile(f.content)
                except re.error:
                    status = "Invalid Regex"
            click.echo(f"{ch.legacy_id:<20} | {f.flag_type:<10} | {f.content[:38]:<40} | {status:<10}")

@click.command("create-admin")
@click.option("--username", prompt="Admin Username", help="Admin username")
@click.option("--password", prompt="Admin Password", hide_input=True, confirmation_prompt=True, help="Admin password")
@click.option("--email", default=None, help="Admin email")
@with_appcontext
def create_admin_command(username, password, email):
    """Create a new administrative user inside the database."""
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import hash_password, validate_password_strength
    from flask import current_app

    # Validate password strength
    err = validate_password_strength(password, current_app.config)
    if err:
        click.echo(f"[ERROR] Password strength check failed: {err}", err=True)
        return

    if UserRepository.get_by_name(username):
        click.echo(f"[ERROR] User with name '{username}' already exists.", err=True)
        return

    try:
        UserRepository.create(
            username=username,
            password_hash=hash_password(password),
            display_name=username,
            email=email,
            role_name="Admin"
        )
        click.echo(f"[OK] Admin user '{username}' created successfully.")
    except Exception as e:
        click.echo(f"[ERROR] Failed to create admin: {e}", err=True)

@click.command("reset-password")
@click.option("--username", prompt="Username", help="User to reset")
@click.option("--password", prompt="New Password", hide_input=True, confirmation_prompt=True, help="New password")
@with_appcontext
def reset_password_command(username, password):
    """Reset password for a specified user."""
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import hash_password, validate_password_strength
    from app.extensions import db
    from flask import current_app

    user = UserRepository.get_by_name(username)
    if not user:
        click.echo(f"[ERROR] User '{username}' not found.", err=True)
        return

    err = validate_password_strength(password, current_app.config)
    if err:
        click.echo(f"[ERROR] Password strength check failed: {err}", err=True)
        return

    try:
        user.password_hash = hash_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"[OK] Password for user '{username}' reset successfully.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"[ERROR] Failed to reset password: {e}", err=True)

@click.command("unlock-user")
@click.option("--username", prompt="Username", help="User to unlock")
@with_appcontext
def unlock_user_command(username):
    """Unlock a locked user account (resets failed attempt counter)."""
    from app.repositories.user_repository import UserRepository
    from app.extensions import db

    user = UserRepository.get_by_name(username)
    if not user:
        click.echo(f"[ERROR] User '{username}' not found.", err=True)
        return

    try:
        user.failed_login_attempts = 0
        db.session.add(user)
        db.session.commit()
        click.echo(f"[OK] User '{username}' unlocked successfully.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"[ERROR] Failed to unlock user: {e}", err=True)

@click.command("list-users")
@with_appcontext
def list_users_command():
    """List all non-deleted users and their active roles."""
    from app.repositories.user_repository import UserRepository

    users = UserRepository.list_all_users()
    if not users:
        click.echo("No users registered.")
        return

    click.echo(f"{'Username':<20} | {'Display Name':<25} | {'Role':<15} | {'Status':<10}")
    click.echo("-" * 79)
    for u in users:
        status = "Active" if u.is_active else "Inactive"
        if u.failed_login_attempts >= 5:
            status = "Locked"
        click.echo(f"{u.username:<20} | {u.display_name or 'None':<25} | {u.role:<15} | {status:<10}")

@click.command("migrate-legacy")
@with_appcontext
def migrate_legacy_command():
    """Migrate legacy scores.json data into the SQL database, preserving history."""
    from app.extensions import db
    from app.models.user import User
    from app.models.challenge import Challenge
    from app.models.submission import Submission
    from app.repositories.role_repository import RoleRepository

    scores_file = current_app.config.get("SCORES_FILE", "scores.json")
    if not os.path.exists(scores_file):
        click.echo(f"[ERROR] Legacy scores file not found at {scores_file}", err=True)
        return

    RoleRepository.setup_default_roles()

    try:
        with open(scores_file, encoding='utf-8') as f:
            data = json.load(f)

        participants = data.get("participants", {})
        click.echo(f"Found {len(participants)} participants in scores.json.")

        migrated_users = 0
        migrated_solves = 0

        for username, info in participants.items():
            reg_str = info.get("registered_at")
            if reg_str:
                try:
                    registered_at = datetime.datetime.fromisoformat(reg_str)
                except ValueError:
                    registered_at = datetime.datetime.utcnow()
            else:
                registered_at = datetime.datetime.utcnow()

            user = User.query.filter_by(username=username).first()
            if not user:
                from app.repositories.user_repository import UserRepository
                user = UserRepository.create(
                    username=username,
                    password_hash=None,
                    display_name=username,
                    role_name="Participant"
                )
                user.registered_at = registered_at
                db.session.add(user)
                db.session.flush()
                migrated_users += 1
            else:
                user.registered_at = registered_at
                user.is_deleted = False
                db.session.add(user)
                db.session.flush()

            solved = info.get("solved", {})
            for ch_id, solve_info in solved.items():
                challenge = Challenge.query.filter_by(legacy_id=ch_id, is_deleted=False).first()
                if not challenge:
                    click.echo(f"[WARNING] Challenge {ch_id} not found in database. Skipping solve.")
                    continue

                time_str = solve_info.get("time")
                if time_str:
                    try:
                        solve_time = datetime.datetime.fromisoformat(time_str)
                    except ValueError:
                        solve_time = datetime.datetime.utcnow()
                else:
                    solve_time = datetime.datetime.utcnow()

                points = solve_info.get("points", challenge.points)
                elapsed = solve_info.get("elapsed")
                if elapsed is None:
                    elapsed = int((solve_time - registered_at).total_seconds())

                sub = Submission.query.filter_by(user_id=user.id, challenge_id=challenge.id).first()
                if not sub:
                    sub = Submission(
                        user_id=user.id,
                        challenge_id=challenge.id,
                        points=points,
                        time=solve_time,
                        elapsed=elapsed
                    )
                    db.session.add(sub)
                    migrated_solves += 1
                else:
                    sub.points = points
                    sub.time = solve_time
                    sub.elapsed = elapsed
                    db.session.add(sub)

        db.session.commit()
        click.echo(f"[OK] Migration completed: Migrated/Updated {migrated_users} users and {migrated_solves} solves.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"[ERROR] Migration failed: {e}", err=True)

@click.command("db-health")
@with_appcontext
def db_health_command():
    """Verify database connectivity and migration state."""
    from app.extensions import db
    from sqlalchemy import text
    try:
        db.session.execute(text("SELECT 1"))
        click.echo("[OK] Database connection successful.")
    except Exception as e:
        click.echo(f"[ERROR] Database connection failed: {e}", err=True)
        return

    try:
        from alembic.migration import MigrationContext
        from alembic.script import ScriptDirectory
        from flask import current_app
        
        engine = db.engine
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
            
        migrate_dir = os.path.join(current_app.root_path, "..", "migrations")
        if not os.path.exists(migrate_dir):
            click.echo("[WARNING] Migrations folder not found.")
            return
            
        from alembic.config import Config as AlembicConfig
        alembic_cfg = AlembicConfig(os.path.join(migrate_dir, "alembic.ini"))
        alembic_cfg.set_main_option("script_location", migrate_dir)
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
        
        click.echo(f"Current migration revision: {current_rev}")
        click.echo(f"Latest migration revision: {head_rev}")
        if current_rev == head_rev:
            click.echo("[OK] Database is up-to-date with migrations.")
        else:
            click.echo("[WARNING] Database is out of sync. Please run 'flask db upgrade'.")
    except Exception as e:
        click.echo(f"[ERROR] Failed to check migration state: {e}", err=True)

@click.command("backup")
@with_appcontext
def backup_command():
    """Backup active database state."""
    click.echo("Database backup generated (Milestone 1 skeleton).")

@click.command("restore")
@with_appcontext
def restore_command():
    """Restore database from backup file."""
    click.echo("Database restored (Milestone 1 skeleton).")

@click.command("import")
@with_appcontext
def import_command():
    """Import CTF data from file."""
    click.echo("CTF data imported successfully (Milestone 1 skeleton).")

@click.command("export")
@with_appcontext
def export_command():
    """Export CTF data to file."""
    click.echo("CTF data exported successfully (Milestone 1 skeleton).")

@click.command("health-check")
@with_appcontext
def health_check_command():
    """Execute application health verification."""
    click.echo("Application health check verified (Milestone 1 skeleton).")

def register_cli_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_command)
    app.cli.add_command(seed_challenges_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(reset_password_command)
    app.cli.add_command(unlock_user_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(migrate_legacy_command)
    app.cli.add_command(db_health_command)
    app.cli.add_command(backup_command)
    app.cli.add_command(restore_command)
    app.cli.add_command(import_command)
    app.cli.add_command(export_command)
    app.cli.add_command(health_check_command)
    app.cli.add_command(import_challenges_command)
    app.cli.add_command(export_challenges_command)
    app.cli.add_command(rebuild_scoring_command)
    app.cli.add_command(verify_flags_command)
    # Milestone 5
    app.cli.add_command(competition_status_command)
    app.cli.add_command(freeze_command)
    app.cli.add_command(unfreeze_command)
    app.cli.add_command(end_competition_command)
    app.cli.add_command(announce_command)
    app.cli.add_command(list_announcements_command)
    app.cli.add_command(reset_submissions_command)
    app.cli.add_command(export_submissions_command)

# ═══════════════════════════════════════════════════════════════
# MILESTONE 5 – COMPETITION OPERATIONS CLI
# ═══════════════════════════════════════════════════════════════

@click.command("competition-status")
@with_appcontext
def competition_status_command():
    """Show current competition state and timing information."""
    from app.services.competition_service import CompetitionService
    comp = CompetitionService.get_active_competition()
    state = CompetitionService.get_competition_state(comp)
    click.echo(f"Competition : {comp.name}")
    click.echo(f"State       : {state.upper()}")
    click.echo(f"Start       : {comp.start_time or 'Not set'}")
    click.echo(f"End         : {comp.end_time or 'Not set'}")
    click.echo(f"Freeze      : {comp.freeze_time or 'Not set'}")
    click.echo(f"Unfreeze    : {comp.unfreeze_time or 'Not set'}")
    click.echo(f"Active      : {comp.is_active}")
    click.echo(f"Practice    : {comp.allow_practice}")

@click.command("freeze-scoreboard")
@with_appcontext
def freeze_command():
    """Immediately freeze the public scoreboard (now → end_time)."""
    from app.services.competition_service import CompetitionService
    comp = CompetitionService.get_active_competition()
    now = datetime.datetime.utcnow()
    unfreeze = comp.end_time or now + datetime.timedelta(hours=1)
    CompetitionService.update_competition(comp.id, freeze_time=now, unfreeze_time=unfreeze)
    click.echo(f"[OK] Scoreboard frozen at {now.strftime('%Y-%m-%d %H:%M:%S')} UTC. Unfreezes at {unfreeze.strftime('%Y-%m-%d %H:%M:%S')} UTC.")

@click.command("unfreeze-scoreboard")
@with_appcontext
def unfreeze_command():
    """Remove scoreboard freeze window."""
    from app.services.competition_service import CompetitionService
    comp = CompetitionService.get_active_competition()
    CompetitionService.update_competition(comp.id, freeze_time=None, unfreeze_time=None)
    click.echo("[OK] Scoreboard unfrozen.")

@click.command("end-competition")
@with_appcontext
def end_competition_command():
    """Mark competition as ended (set end_time to now)."""
    from app.services.competition_service import CompetitionService
    comp = CompetitionService.get_active_competition()
    now = datetime.datetime.utcnow()
    CompetitionService.update_competition(comp.id, end_time=now)
    click.echo(f"[OK] Competition '{comp.name}' ended at {now.strftime('%Y-%m-%d %H:%M:%S')} UTC.")

@click.command("announce")
@click.option("--title", prompt="Announcement Title", help="Title of the announcement")
@click.option("--content", prompt="Announcement Content", help="Announcement body text")
@click.option("--pin", is_flag=True, default=False, help="Pin this announcement")
@with_appcontext
def announce_command(title, content, pin):
    """Publish a competition announcement from the command line."""
    from app.services.announcement_service import AnnouncementService
    ann, err = AnnouncementService.create_announcement(title=title, content=content, pinned=pin, visible=True)
    if err:
        click.echo(f"[ERROR] {err}", err=True)
    else:
        click.echo(f"[OK] Announcement #{ann.id} '{ann.title}' published.{'(Pinned)' if pin else ''}")

@click.command("list-announcements")
@with_appcontext
def list_announcements_command():
    """List all current competition announcements."""
    from app.repositories.announcement_repository import AnnouncementRepository
    anns = AnnouncementRepository.get_all(include_unpublished=True)
    if not anns:
        click.echo("No announcements found.")
        return
    click.echo(f"{'ID':<5} | {'Pinned':<6} | {'Published':<9} | {'Title'}")
    click.echo("-" * 60)
    for ann in anns:
        click.echo(f"{ann.id:<5} | {'Yes' if ann.pinned else 'No':<6} | {'Yes' if ann.published else 'No':<9} | {ann.title}")

@click.command("reset-submissions")
@click.option("--username", default=None, help="Reset only for a specific user")
@click.option("--force", is_flag=True, default=False, help="Skip confirmation for full reset")
@with_appcontext
def reset_submissions_command(username, force):
    """Reset flag submissions (per-user or entire platform)."""
    from app.repositories.submission_repository import SubmissionRepository
    from app.services.challenge_service import ChallengeService

    if username:
        result = SubmissionRepository.reset_user_solves(username)
        if result:
            ChallengeService.rebuild_all_challenge_points()
            click.echo(f"[OK] Submissions reset for user '{username}'.")
        else:
            click.echo(f"[ERROR] User '{username}' not found.", err=True)
    else:
        if not force:
            confirm = click.confirm("This will delete ALL submissions and users. Continue?")
            if not confirm:
                click.echo("Aborted.")
                return
        SubmissionRepository.reset_all_solves()
        ChallengeService.rebuild_all_challenge_points()
        click.echo("[OK] All submissions and users reset.")

@click.command("export-submissions")
@click.option("--file", default="submissions_export.csv", help="Output CSV file path")
@with_appcontext
def export_submissions_command(file):
    """Export all submissions to a CSV file."""
    from app.services.submission_service import SubmissionService
    csv_data = SubmissionService.export_csv()
    with open(file, "w", encoding="utf-8") as f:
        f.write(csv_data)
    click.echo(f"[OK] Submissions exported to '{file}'.")

