"""extend_competition_announcement_submission

Revision ID: 38bc69795002
Revises: c617c6404487
Create Date: 2026-07-01 12:27:23.768306

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '38bc69795002'
down_revision = 'c617c6404487'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c['name'] for c in insp.get_columns(table_name)]
    return column_name in columns

def upgrade():
    with op.batch_alter_table('announcements', schema=None) as batch_op:
        if not column_exists('announcements', 'scheduled_at'):
            batch_op.add_column(sa.Column('scheduled_at', sa.DateTime(), nullable=True))
        if not column_exists('announcements', 'pinned'):
            batch_op.add_column(sa.Column('pinned', sa.Boolean(), server_default='0', nullable=False))
        if not column_exists('announcements', 'published'):
            batch_op.add_column(sa.Column('published', sa.Boolean(), server_default='1', nullable=False))
        if not column_exists('announcements', 'visibility'):
            batch_op.add_column(sa.Column('visibility', sa.String(length=20), server_default='public', nullable=False))

    with op.batch_alter_table('competitions', schema=None) as batch_op:
        if not column_exists('competitions', 'description'):
            batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        if not column_exists('competitions', 'start_time'):
            batch_op.add_column(sa.Column('start_time', sa.DateTime(), nullable=True))
        if not column_exists('competitions', 'end_time'):
            batch_op.add_column(sa.Column('end_time', sa.DateTime(), nullable=True))
        if not column_exists('competitions', 'registration_open'):
            batch_op.add_column(sa.Column('registration_open', sa.DateTime(), nullable=True))
        if not column_exists('competitions', 'registration_close'):
            batch_op.add_column(sa.Column('registration_close', sa.DateTime(), nullable=True))
        if not column_exists('competitions', 'freeze_time'):
            batch_op.add_column(sa.Column('freeze_time', sa.DateTime(), nullable=True))
        if not column_exists('competitions', 'unfreeze_time'):
            batch_op.add_column(sa.Column('unfreeze_time', sa.DateTime(), nullable=True))
        if not column_exists('competitions', 'is_active'):
            batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False))
        if not column_exists('competitions', 'is_paused'):
            batch_op.add_column(sa.Column('is_paused', sa.Boolean(), server_default='0', nullable=False))
        if not column_exists('competitions', 'is_archived'):
            batch_op.add_column(sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False))
        if not column_exists('competitions', 'visibility'):
            batch_op.add_column(sa.Column('visibility', sa.String(length=20), server_default='public', nullable=False))
        if not column_exists('competitions', 'allow_practice'):
            batch_op.add_column(sa.Column('allow_practice', sa.Boolean(), server_default='1', nullable=False))
        if not column_exists('competitions', 'max_attempts'):
            batch_op.add_column(sa.Column('max_attempts', sa.Integer(), server_default='0', nullable=False))
        if not column_exists('competitions', 'rules'):
            batch_op.add_column(sa.Column('rules', sa.Text(), nullable=True))
        if not column_exists('competitions', 'banner'):
            batch_op.add_column(sa.Column('banner', sa.String(length=255), nullable=True))
        if not column_exists('competitions', 'created_by'):
            batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_competitions_created_by', 'users', ['created_by'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('submissions', schema=None) as batch_op:
        if not column_exists('submissions', 'submitted_flag'):
            batch_op.add_column(sa.Column('submitted_flag', sa.String(length=255), nullable=True))
        if not column_exists('submissions', 'correct'):
            batch_op.add_column(sa.Column('correct', sa.Boolean(), server_default='1', nullable=False))
        if not column_exists('submissions', 'status'):
            batch_op.add_column(sa.Column('status', sa.String(length=20), server_default='correct', nullable=False))

def downgrade():
    with op.batch_alter_table('submissions', schema=None) as batch_op:
        if column_exists('submissions', 'status'):
            batch_op.drop_column('status')
        if column_exists('submissions', 'correct'):
            batch_op.drop_column('correct')
        if column_exists('submissions', 'submitted_flag'):
            batch_op.drop_column('submitted_flag')

    with op.batch_alter_table('competitions', schema=None) as batch_op:
        if column_exists('competitions', 'created_by'):
            batch_op.drop_constraint('fk_competitions_created_by', type_='foreignkey')
            batch_op.drop_column('created_by')
        if column_exists('competitions', 'banner'):
            batch_op.drop_column('banner')
        if column_exists('competitions', 'rules'):
            batch_op.drop_column('rules')
        if column_exists('competitions', 'max_attempts'):
            batch_op.drop_column('max_attempts')
        if column_exists('competitions', 'allow_practice'):
            batch_op.drop_column('allow_practice')
        if column_exists('competitions', 'visibility'):
            batch_op.drop_column('visibility')
        if column_exists('competitions', 'is_archived'):
            batch_op.drop_column('is_archived')
        if column_exists('competitions', 'is_paused'):
            batch_op.drop_column('is_paused')
        if column_exists('competitions', 'is_active'):
            batch_op.drop_column('is_active')
        if column_exists('competitions', 'unfreeze_time'):
            batch_op.drop_column('unfreeze_time')
        if column_exists('competitions', 'freeze_time'):
            batch_op.drop_column('freeze_time')
        if column_exists('competitions', 'registration_close'):
            batch_op.drop_column('registration_close')
        if column_exists('competitions', 'registration_open'):
            batch_op.drop_column('registration_open')
        if column_exists('competitions', 'end_time'):
            batch_op.drop_column('end_time')
        if column_exists('competitions', 'start_time'):
            batch_op.drop_column('start_time')
        if column_exists('competitions', 'description'):
            batch_op.drop_column('description')

    with op.batch_alter_table('announcements', schema=None) as batch_op:
        if column_exists('announcements', 'visibility'):
            batch_op.drop_column('visibility')
        if column_exists('announcements', 'published'):
            batch_op.drop_column('published')
        if column_exists('announcements', 'pinned'):
            batch_op.drop_column('pinned')
        if column_exists('announcements', 'scheduled_at'):
            batch_op.drop_column('scheduled_at')
