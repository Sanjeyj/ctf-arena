from app.extensions import db
from app.models.category import Category

class CategoryRepository:
    @staticmethod
    def get_by_id(cat_id):
        return Category.query.get(cat_id)

    @staticmethod
    def get_by_name(name):
        return Category.query.filter_by(name=name).first()

    @staticmethod
    def get_all(include_hidden=True):
        q = Category.query
        if not include_hidden:
            q = q.filter_by(visible=True)
        return q.order_by(Category.display_order.asc(), Category.id.asc()).all()

    @staticmethod
    def create(name, description=None, color="#00f0ff", icon=None, display_order=0, visible=True):
        cat = Category(
            name=name,
            description=description,
            color=color,
            icon=icon,
            display_order=display_order,
            visible=visible
        )
        db.session.add(cat)
        db.session.commit()
        return cat

    @staticmethod
    def update(cat, **kwargs):
        for k, v in kwargs.items():
            if hasattr(cat, k):
                setattr(cat, k, v)
        db.session.commit()
        return cat

    @staticmethod
    def delete(cat):
        db.session.delete(cat)
        db.session.commit()
