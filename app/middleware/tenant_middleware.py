from flask import request, g
from app.models.organization import Organization

class TenantContext:
    """Context manager to scope a block of code to a specific organization (useful for testing)."""
    def __init__(self, org):
        self.org = org
        self.old_org = None

    def __enter__(self):
        self.old_org = getattr(g, 'current_org', None)
        g.current_org = self.org
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        g.current_org = self.old_org


class OrganizationResolverMiddleware:
    """Middleware/helper to resolve organization from the host subdomain."""
    @staticmethod
    def resolve_tenant():
        # Check if current_org is already set (e.g. by TenantContext in tests)
        if getattr(g, 'current_org', None) is not None:
            return

        host = request.headers.get('Host', '')
        # Remove port if present
        host_name = host.split(':')[0]
        parts = host_name.split('.')

        subdomain = None
        # E.g. acme.ctfarena.local -> ['acme', 'ctfarena', 'local'] (len 3)
        # E.g. acme.localhost -> ['acme', 'localhost'] (len 2)
        if len(parts) >= 3:
            subdomain = parts[0]
        elif len(parts) == 2 and 'localhost' in parts[1]:
            subdomain = parts[0]

        g.current_org = None
        if subdomain and subdomain not in ('www', 'api', 'admin'):
            org = Organization.query.filter_by(slug=subdomain, is_deleted=False).first()
            if org:
                g.current_org = org
