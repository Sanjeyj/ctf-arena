from app.repositories.category_repository import CategoryRepository

class CategoryService:
    @staticmethod
    def get_all_categories(include_hidden=True):
        return CategoryRepository.get_all(include_hidden=include_hidden)

    @staticmethod
    def get_category_by_id(cat_id):
        return CategoryRepository.get_by_id(cat_id)

    @staticmethod
    def create_category(name, description=None, color="#00f0ff", icon=None, display_order=0, visible=True):
        name = name.strip()
        if not name:
            return None, "Category name cannot be empty."
        if CategoryRepository.get_by_name(name):
            return None, f"Category '{name}' already exists."
        cat = CategoryRepository.create(name, description, color, icon, display_order, visible)
        return cat, None

    @staticmethod
    def update_category(cat_id, **kwargs):
        cat = CategoryRepository.get_by_id(cat_id)
        if not cat:
            return None, "Category not found."
        
        name = kwargs.get("name")
        if name is not None:
            name = name.strip()
            if not name:
                return None, "Category name cannot be empty."
            existing = CategoryRepository.get_by_name(name)
            if existing and existing.id != cat_id:
                return None, f"Category '{name}' already exists."
            kwargs["name"] = name

        updated = CategoryRepository.update(cat, **kwargs)
        return updated, None

    @staticmethod
    def delete_category(cat_id):
        cat = CategoryRepository.get_by_id(cat_id)
        if not cat:
            return False, "Category not found."
        CategoryRepository.delete(cat)
        return True, None
