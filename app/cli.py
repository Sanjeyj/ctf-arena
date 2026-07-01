import click
from flask.cli import with_appcontext

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    click.echo("Initialized the database (Milestone 1 skeleton).")

@click.command("seed")
@with_appcontext
def seed_command():
    """Seed existing challenges and categories."""
    click.echo("Seeded default database content (Milestone 1 skeleton).")

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

@click.command("create-admin")
@with_appcontext
def create_admin_command():
    """Create a new administrative user."""
    click.echo("Admin user created (Milestone 1 skeleton).")

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
    app.cli.add_command(backup_command)
    app.cli.add_command(restore_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(import_command)
    app.cli.add_command(export_command)
    app.cli.add_command(health_check_command)
