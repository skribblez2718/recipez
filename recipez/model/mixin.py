from typing import Any, Dict


###################################[ start AsDictMixin ]###################################
class AsDictMixin:
    """
    Mixin to add an as_dict() method to SQLAlchemy models.

    Returns a dictionary of the model's column names and values.
    """

    def as_dict(self) -> Dict[str, Any]:
        """
        Convert the SQLAlchemy model instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary mapping column names to values.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


###################################[ end AsDictMixin ]###################################
