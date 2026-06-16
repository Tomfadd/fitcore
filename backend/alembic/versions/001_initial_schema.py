"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('height_cm', sa.Float(), nullable=False),
        sa.Column('bmi', sa.Float(), nullable=False),
        sa.Column('rfm', sa.Float(), nullable=False),
        sa.Column('goal', sa.String(50), nullable=False),
        sa.Column('conditions', JSON, default=list),
        sa.Column('points', sa.Integer(), default=0),
        sa.Column('streak', sa.Integer(), default=0),
        sa.Column('last_workout_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('exercises',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(120), unique=True, nullable=False),
        sa.Column('category', sa.String(60), nullable=False),
        sa.Column('icon', sa.String(10), default='🏋️'),
        sa.Column('met_value', sa.Float(), nullable=False),
        sa.Column('intensity_level', sa.String(20), nullable=False),
        sa.Column('muscle_groups', sa.String(255)),
        sa.Column('equipment', sa.String(120)),
        sa.Column('safe_for', JSON, default=list),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('workout_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('logged_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('duration_mins', sa.Integer(), default=30),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('perceived_effort', sa.Integer()),
        sa.Column('heart_rate_avg', sa.Integer()),
        sa.Column('calories_burned', sa.Integer()),
        sa.Column('notes', sa.Text()),
    )
    op.create_table('recommendations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('recommended_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('source', sa.String(30), default='hybrid'),
        sa.Column('content_score', sa.Float()),
        sa.Column('collab_score', sa.Float()),
        sa.Column('adherence_score', sa.Float()),
        sa.Column('final_score', sa.Float()),
        sa.Column('rnn_adaptation', sa.String(20)),
    )
    op.create_table('rewards',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('badge_id', sa.String(50), nullable=False),
        sa.Column('badge_name', sa.String(120)),
        sa.Column('points', sa.Integer(), default=0),
        sa.Column('earned_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('safety_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('rule_fired', sa.String(120)),
        sa.Column('reason', sa.Text()),
        sa.Column('logged_at', sa.DateTime(), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('safety_audit_logs')
    op.drop_table('rewards')
    op.drop_table('recommendations')
    op.drop_table('workout_logs')
    op.drop_table('exercises')
    op.drop_table('users')
