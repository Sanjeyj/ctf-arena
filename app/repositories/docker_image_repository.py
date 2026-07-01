from app.extensions import db
from app.models.docker_image import DockerImage


class DockerImageRepository:
    """CRUD access for DockerImage records."""

    @staticmethod
    def get_all():
        return DockerImage.query.order_by(DockerImage.created_at.desc()).all()

    @staticmethod
    def get_by_id(image_id):
        return DockerImage.query.get(image_id)

    @staticmethod
    def get_by_name_tag(name, tag='latest'):
        return DockerImage.query.filter_by(name=name, tag=tag).first()

    @staticmethod
    def create(name, tag='latest', registry=None, description=None, size_bytes=None):
        img = DockerImage(
            name=name,
            tag=tag,
            registry=registry,
            description=description,
            size_bytes=size_bytes,
        )
        db.session.add(img)
        db.session.commit()
        return img

    @staticmethod
    def update(image_id, **kwargs):
        img = DockerImage.query.get(image_id)
        if not img:
            return None
        for k, v in kwargs.items():
            setattr(img, k, v)
        db.session.commit()
        return img

    @staticmethod
    def delete(image_id):
        img = DockerImage.query.get(image_id)
        if img:
            db.session.delete(img)
            db.session.commit()
        return img
