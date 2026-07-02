"""
Threat Intelligence Service — Phase 18 SOC Platform.
IOC management, enrichment, correlation, and feed aggregation (simulation only).
"""
import datetime
import random
import hashlib
from app.extensions import db
from app.models.ioc import IOC, IOC_TYPES, IOC_SEVERITIES
from app.models.threat_feed import ThreatFeed


# Simulated geo/reputation database
_GEO_DB = {
    'ip': ['US', 'CN', 'RU', 'IR', 'KP', 'BR', 'DE', 'FR', 'GB'],
    'domain': ['US', 'RU', 'CN', 'NL', 'DE'],
}

_MALICIOUS_PATTERNS = ['malware', 'phish', 'c2', 'botnet', 'ransom', 'exploit']


class ThreatIntelligenceService:

    # -------------------------------------------------------------------------
    # IOC Management
    # -------------------------------------------------------------------------

    @staticmethod
    def create_ioc(ioc_type: str, value: str, severity: str = 'medium',
                   confidence: int = 50, source: str = 'manual',
                   org_id: int = None, tags: str = '', description: str = '') -> IOC:
        """Create a new IOC record."""
        if ioc_type not in IOC_TYPES:
            raise ValueError(f"Invalid IOC type '{ioc_type}'. Must be one of {IOC_TYPES}")
        if severity not in IOC_SEVERITIES:
            raise ValueError(f"Invalid severity '{severity}'.")
        confidence = max(0, min(100, confidence))

        ioc = IOC(
            type=ioc_type,
            value=value,
            severity=severity,
            confidence=confidence,
            source=source,
            organization_id=org_id,
            tags=tags,
            description=description,
        )
        db.session.add(ioc)
        db.session.commit()
        return ioc

    @staticmethod
    def get_ioc(ioc_id: int) -> IOC:
        return db.session.get(IOC, ioc_id)

    @staticmethod
    def list_iocs(org_id: int = None, ioc_type: str = None, severity: str = None,
                  active_only: bool = True):
        q = IOC.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        if ioc_type:
            q = q.filter_by(type=ioc_type)
        if severity:
            q = q.filter_by(severity=severity)
        if active_only:
            q = q.filter_by(is_active=True)
        return q.order_by(IOC.created_at.desc()).all()

    @staticmethod
    def update_ioc(ioc_id: int, **kwargs) -> IOC:
        ioc = db.session.get(IOC, ioc_id)
        if not ioc:
            raise ValueError(f"IOC {ioc_id} not found")
        for key, val in kwargs.items():
            if hasattr(ioc, key):
                setattr(ioc, key, val)
        ioc.last_seen = datetime.datetime.utcnow()
        db.session.commit()
        return ioc

    # -------------------------------------------------------------------------
    # IOC Enrichment (simulated)
    # -------------------------------------------------------------------------

    @staticmethod
    def enrich_ioc(ioc_id: int) -> dict:
        """
        Simulate IOC enrichment with geo/reputation data.
        NO live network requests — purely educational simulation.
        """
        ioc = db.session.get(IOC, ioc_id)
        if not ioc:
            raise ValueError(f"IOC {ioc_id} not found")

        # Simulated geo lookup
        geo_pool = _GEO_DB.get(ioc.type, ['US', 'RU', 'CN'])
        geo_country = random.choice(geo_pool)

        # Reputation score: lower = more malicious (0–100)
        base_score = 85
        if any(p in ioc.value.lower() for p in _MALICIOUS_PATTERNS):
            base_score = random.randint(5, 30)
        elif ioc.severity == 'critical':
            base_score = random.randint(0, 20)
        elif ioc.severity == 'high':
            base_score = random.randint(10, 40)
        elif ioc.severity == 'medium':
            base_score = random.randint(30, 60)
        else:
            base_score = random.randint(60, 90)

        ioc.geo_country = geo_country
        ioc.reputation_score = base_score
        ioc.enriched_at = datetime.datetime.utcnow()
        ioc.last_seen = datetime.datetime.utcnow()
        db.session.commit()

        return {
            'ioc_id': ioc_id,
            'geo_country': geo_country,
            'reputation_score': base_score,
            'enriched_at': ioc.enriched_at.isoformat(),
            'verdict': 'malicious' if base_score < 40 else 'suspicious' if base_score < 70 else 'benign',
        }

    # -------------------------------------------------------------------------
    # IOC Correlation (simulated)
    # -------------------------------------------------------------------------

    @staticmethod
    def correlate_iocs(org_id: int = None) -> list:
        """
        Find IOC clusters that share attributes (source, tags, severity).
        Returns groups of correlated IOC IDs.
        """
        iocs = ThreatIntelligenceService.list_iocs(org_id=org_id)
        clusters = {}
        for ioc in iocs:
            key = f"{ioc.source}:{ioc.severity}"
            clusters.setdefault(key, []).append(ioc.id)

        # Only return clusters with >1 IOC
        return [
            {'cluster_key': k, 'ioc_ids': v, 'size': len(v)}
            for k, v in clusters.items() if len(v) > 1
        ]

    # -------------------------------------------------------------------------
    # Feed Aggregation (simulated)
    # -------------------------------------------------------------------------

    @staticmethod
    def aggregate_feeds(org_id: int = None) -> dict:
        """
        Simulate pulling IOCs from enabled threat feeds.
        Creates synthetic IOC records for educational demonstration.
        NO live network requests.
        """
        feeds = ThreatFeed.query.filter_by(enabled=True)
        if org_id:
            feeds = feeds.filter_by(organization_id=org_id)
        feeds = feeds.all()

        total_new = 0
        results = []
        for feed in feeds:
            # Simulate 2–5 new IOCs per feed pull
            count = random.randint(2, 5)
            for i in range(count):
                ioc_type = random.choice(['ip', 'domain', 'url'])
                fake_value = f"sim-{hashlib.md5(f'{feed.id}-{i}'.encode()).hexdigest()[:8]}.example"
                ThreatIntelligenceService.create_ioc(
                    ioc_type=ioc_type,
                    value=fake_value,
                    severity=random.choice(['low', 'medium', 'high']),
                    confidence=random.randint(40, 90),
                    source=feed.name,
                    org_id=org_id,
                )
            feed.last_fetched = datetime.datetime.utcnow()
            feed.ioc_count = (feed.ioc_count or 0) + count
            total_new += count
            results.append({'feed': feed.name, 'new_iocs': count})

        db.session.commit()
        return {'feeds_processed': len(feeds), 'total_new_iocs': total_new, 'details': results}

    # -------------------------------------------------------------------------
    # Feed Management
    # -------------------------------------------------------------------------

    @staticmethod
    def create_feed(name: str, url: str = None, feed_type: str = 'open_source',
                    org_id: int = None) -> ThreatFeed:
        feed = ThreatFeed(
            name=name,
            url=url,
            feed_type=feed_type,
            organization_id=org_id,
        )
        db.session.add(feed)
        db.session.commit()
        return feed
