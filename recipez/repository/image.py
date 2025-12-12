from typing import Optional, List
from recipez import sqla_db
from recipez.model import RecipezImageModel


#####################################[ start ImageRepository ]####################################
class ImageRepository:
    """
    Repository for image-related database operations using SQLAlchemy.

    This class provides methods to interact with the Image model in the database,
    replacing raw SQL queries with SQLAlchemy ORM operations.
    """

    #########################[ start create_image ]#########################
    @staticmethod
    def create_image(url: str, author_id: str) -> RecipezImageModel:
        """
        Create a new image in the database.

        Args:
            url (str): The URL of the image.
            author_id (str): The ID of the author who uploaded this image.

        Returns:
            RecipezImageModel: The created image object.
        """
        image = RecipezImageModel(image_url=url, image_author_id=author_id)
        sqla_db.session.add(image)
        sqla_db.session.commit()

        return image

    #########################[ end create_image ]#########################

    #########################[ start read_image_by_id ]#########################
    @staticmethod
    def read_image_by_id(image_id: str) -> Optional[RecipezImageModel]:
        """
        Get an image by its ID.

        Args:
            image_id (str): The ID of the image to retrieve.

        Returns:
            Optional[RecipezImageModel]: The image object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezImageModel)
            .filter_by(image_id=image_id)
            .first()
        )

    #########################[ end read_image_by_id ]#########################

    #########################[ start read_all_images ]#########################
    @staticmethod
    def read_all_images() -> List[RecipezImageModel]:
        """
        Get all images from the database.

        Returns:
            List[RecipezImageModel]: A list of all image objects.
        """
        return sqla_db.session.query(RecipezImageModel).all()

    #########################[ end read_all_images ]#########################

    #########################[ start read_images_by_author_id ]#########################
    @staticmethod
    def read_images_by_author_id(author_id: str) -> List[RecipezImageModel]:
        """
        Get all images uploaded by a specific author.

        Args:
            author_id (str): The ID of the author.

        Returns:
            List[RecipezImageModel]: A list of image objects uploaded by the author.
        """
        return (
            sqla_db.session.query(RecipezImageModel)
            .filter_by(image_author_id=author_id)
            .all()
        )

    #########################[ end read_images_by_author_id ]#########################

    #########################[ start update_image ]#########################
    @staticmethod
    def update_image(image_id: str, url: str) -> bool:
        """
        Update an image in the database.

        Args:
            image_id (str): The ID of the image to update.
            url (str): The new URL of the image.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        image = ImageRepository.read_image_by_id(image_id)
        if image:
            image.image_url = url
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_image ]#########################

    #########################[ start delete_image ]#########################
    @staticmethod
    def delete_image(image_id: str) -> bool:
        """
        Delete an image from the database and filesystem.

        Args:
            image_id (str): The ID of the image to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.

        Note:
            Default images (default_recipe.png, default_user.png) are never deleted
            from the filesystem, even if their database record is removed.
        """
        image = ImageRepository.read_image_by_id(image_id)
        if image:
            # Store image URL for file deletion
            image_url = image.image_url

            # Delete from database first
            sqla_db.session.delete(image)
            sqla_db.session.commit()

            # Delete file from filesystem (skip default images)
            try:
                import os
                from flask import current_app
                if image_url:
                    # NEVER delete default images - they are shared resources
                    if "default_recipe.png" in image_url or "default_user.png" in image_url:
                        return True

                    filename = os.path.basename(image_url)
                    file_path = os.path.join(current_app.static_folder, 'uploads', filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            except Exception as e:
                # Log error but don't fail the database deletion
                print(f"Warning: Could not delete image file {image_url}: {str(e)}")

            return True
        return False

    #########################[ end delete_image ]#########################

    #########################[ start is_image_author ]#########################
    @staticmethod
    def is_image_author(image_id: str, author_id: str) -> bool:
        """
        Check if a user is the author of an image.

        Args:
            image_id (str): The ID of the image.
            author_id (str): The ID of the user to check.

        Returns:
            bool: True if the user is the author, False otherwise.
        """
        image = ImageRepository.read_image_by_id(image_id)
        return image is not None and image.image_author_id == author_id

    #########################[ end is_image_author ]#########################

    #########################[ start is_image_used_by_recipes ]#########################
    @staticmethod
    def is_image_used_by_recipes(image_id: str) -> bool:
        """
        Check if an image is being used by any recipes.

        Args:
            image_id (str): The ID of the image to check.

        Returns:
            bool: True if the image is used by one or more recipes, False otherwise.
        """
        from recipez.model import RecipezRecipeModel
        count = (
            sqla_db.session.query(RecipezRecipeModel)
            .filter_by(recipe_image_id=image_id)
            .count()
        )
        return count > 0

    #########################[ end is_image_used_by_recipes ]#########################


#####################################[ end ImageRepository ]####################################
