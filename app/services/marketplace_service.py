"""
Marketplace Service - Phase 20 Marketplace.
Handles creation and purchases of courses, labs, plugins, templates, and reports.
"""
from app.extensions import db
from app.models.marketplace_category import MarketplaceCategory
from app.models.marketplace_item import MarketplaceItem
from app.models.marketplace_purchase import MarketplacePurchase
from app.models.user import User

class MarketplaceService:

    @staticmethod
    def create_category(name: str, description: str = "", org_id: int = None) -> MarketplaceCategory:
        cat = MarketplaceCategory(name=name, description=description, organization_id=org_id)
        db.session.add(cat)
        db.session.commit()
        return cat

    @staticmethod
    def create_item(category_id: int, name: str, description: str = "",
                    price: int = 0, asset_type: str = 'courses',
                    asset_url: str = "", org_id: int = None) -> MarketplaceItem:
        item = MarketplaceItem(
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            asset_type=asset_type,
            asset_url=asset_url,
            organization_id=org_id
        )
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def purchase_item(item_id: int, user_id: int, org_id: int = None) -> MarketplacePurchase:
        item = db.session.get(MarketplaceItem, item_id)
        if not item or not item.is_active:
            raise ValueError("Item not found or inactive")
            
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found")
            
        purchase = MarketplacePurchase(
            item_id=item_id,
            user_id=user_id,
            purchase_price=item.price,
            status='completed',
            organization_id=org_id
        )
        db.session.add(purchase)
        db.session.commit()
        return purchase

    @staticmethod
    def list_purchases(user_id: int):
        return MarketplacePurchase.query.filter_by(user_id=user_id).all()
