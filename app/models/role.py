from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Role(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Many-to-many relationship with Permission
    permissions = db.relationship(
        'Permission',
        secondary='role_permissions',
        back_populates='roles',
        lazy='joined'
    )
    
    # Many-to-many relationship with User
    users = db.relationship(
        'User',
        secondary='user_roles',
        back_populates='roles',
        lazy='dynamic'
    )

class Permission(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    roles = db.relationship(
        'Role',
        secondary='role_permissions',
        back_populates='permissions',
        lazy='dynamic'
    )

class UserRole(db.Model, TimestampMixin):
    __tablename__ = 'user_roles'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)

class RolePermission(db.Model, TimestampMixin):
    __tablename__ = 'role_permissions'
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
