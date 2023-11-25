"""Added Interaction model and user fields

Revision ID: f25cfa89e9c0
Revises: cf3bbe72064f
Create Date: 2023-08-16 16:53:37.605114

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f25cfa89e9c0'
down_revision = 'cf3bbe72064f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('interaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('book_title', sa.String(length=100), nullable=False),
    sa.Column('interaction_type', sa.String(length=20), nullable=False),
    sa.Column('rating', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preferred_genres', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('preferred_genres')

    op.drop_table('interaction')
    # ### end Alembic commands ###