"""
Unit and Integration tests for Step 3 Marketplace.
"""
import pytest
import json
from app.extensions import db
from app.models.marketplace_category import MarketplaceCategory
from app.models.marketplace_item import MarketplaceItem
from app.models.marketplace_purchase import MarketplacePurchase
from app.models.organization import Organization
from app.models.user import User
from app.services.marketplace_service import MarketplaceService
from app.services.auth_service import hash_password
from app.research.routes import create_jwt

@pytest.fixture
def market_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(MarketplacePurchase).delete()
        db.session.query(MarketplaceItem).delete()
        db.session.query(MarketplaceCategory).delete()
        db.session.commit()

        org = Organization(name="Market Org", slug="market-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        user = User(username="market_buyer", email="buyer@market.net", password_hash=hash_password("buyer123"))
        db.session.add(user)
        db.session.commit()

        cat = MarketplaceService.create_category("Cyber Ranges", "Virtual sandbox environments", org_id=org.id)

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "market_buyer"}, secret)

        yield {
            "org": org,
            "user": user,
            "category": cat,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_marketplace_items_creation(app, market_setup):
    """Test creating marketplace item model."""
    with app.app_context():
        cat = market_setup['category']
        org = market_setup['org']
        
        item = MarketplaceService.create_item(
            category_id=cat.id,
            name="Intermediate Malware Analysis Range",
            description="Reversing Trojan instances sandbox",
            price=150,
            asset_type="labs",
            asset_url="http://assets.ctf.arena/labs/1",
            org_id=org.id
        )
        assert item.id is not None
        assert item.price == 150
        assert item.asset_type == "labs"

def test_marketplace_purchase_lifecycle(app, market_setup):
    """Test purchasing items through MarketplaceService."""
    with app.app_context():
        cat = market_setup['category']
        user = market_setup['user']
        org = market_setup['org']

        item = MarketplaceService.create_item(
            category_id=cat.id, name="CTI Report APT29", price=45, asset_type="reports", org_id=org.id
        )

        purchase = MarketplaceService.purchase_item(item.id, user.id, org_id=org.id)
        assert purchase.id is not None
        assert purchase.purchase_price == 45
        assert purchase.status == "completed"

        # Check list purchases
        purchases = MarketplaceService.list_purchases(user.id)
        assert len(purchases) == 1
        assert purchases[0].item_id == item.id

def test_marketplace_api_endpoints(client, market_setup):
    """Test GET /api/v1/marketplace REST route."""
    headers = market_setup['headers']
    cat = market_setup['category']
    org = market_setup['org']

    # Seed an item
    resp = client.get('/api/v1/marketplace', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 0

    # Create item
    with client.application.app_context():
        MarketplaceService.create_item(category_id=cat.id, name="Docker Plugin", price=200, org_id=org.id)

    resp = client.get('/api/v1/marketplace', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 1
    assert json.loads(resp.data)['marketplace_items'][0]['price'] == 200


def test_marketplace_category_uniqueness(app, market_setup):
    """Test category creation fails if the category name is already registered."""
    with app.app_context():
        from sqlalchemy.exc import IntegrityError
        # Creating exact duplicate should raise SQL integrity violation
        with pytest.raises(IntegrityError):
            MarketplaceService.create_category("Cyber Ranges")


def test_marketplace_item_inactive_purchase_fails(app, market_setup):
    """Test purchasing inactive items raises ValueError."""
    with app.app_context():
        cat = market_setup['category']
        user = market_setup['user']
        org = market_setup['org']
        
        item = MarketplaceService.create_item(category_id=cat.id, name="Inactive Range", price=10, org_id=org.id)
        item.is_active = False
        db.session.commit()
        
        with pytest.raises(ValueError):
            MarketplaceService.purchase_item(item.id, user.id, org_id=org.id)


def test_marketplace_purchase_nonexistent_user_fails(app, market_setup):
    """Test purchasing with invalid user ID raises ValueError."""
    with app.app_context():
        cat = market_setup['category']
        org = market_setup['org']
        item = MarketplaceService.create_item(category_id=cat.id, name="Item A", price=10, org_id=org.id)
        with pytest.raises(ValueError):
            MarketplaceService.purchase_item(item.id, 9999, org_id=org.id)


def test_marketplace_purchase_nonexistent_item_fails(app, market_setup):
    """Test purchasing invalid item ID raises ValueError."""
    with app.app_context():
        user = market_setup['user']
        org = market_setup['org']
        with pytest.raises(ValueError):
            MarketplaceService.purchase_item(9999, user.id, org_id=org.id)

