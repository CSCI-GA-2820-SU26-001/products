"""
Models for Product

All of the models are stored in this module
"""

import logging
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class Product(db.Model):
    """
    Class that represents a Product
    """

    __tablename__ = "products"
    __table_args__ = {"schema": "product"}

    ##################################################
    # Table Schema
    ##################################################
    sku = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image = db.Column(db.String(2000), nullable=False)

    def __repr__(self):
        return f"<Product {self.name} sku=[{self.sku}]>"

    # def create(self):
    #     """
    #     Creates a Product to the database
    #     """
    #     logger.info("Creating %s", self.name)
    #     try:
    #         db.session.add(self)
    #         db.session.commit()
    #     except Exception as e:
    #         db.session.rollback()
    #         logger.error("Error creating record: %s", self)
    #         raise DataValidationError(e) from e

    # def serialize(self):
    #     """Serializes a Product into a dictionary"""
    #     return {
    #         "sku": self.sku,
    #         "name": self.name,
    #         "description": self.description,
    #         "price": float(self.price),
    #         "image": self.image,
    #     }

    # def deserialize(self, data):
    #     """
    #     Deserializes a Product from a dictionary

    #     Args:
    #         data (dict): A dictionary containing the resource data
    #     """
    #     try:
    #         self.sku = data["sku"]
    #         self.name = data["name"]
    #         self.description = data["description"]
    #         self.price = data["price"]
    #         self.image = data["image"]
    #     except AttributeError as error:
    #         raise DataValidationError("Invalid attribute: " + error.args[0]) from error
    #     except KeyError as error:
    #         raise DataValidationError(
    #             "Invalid Product: missing " + error.args[0]
    #         ) from error
    #     except TypeError as error:
    #         raise DataValidationError(
    #             "Invalid Product: body of request contained bad or no data "
    #             + str(error)
    #         ) from error
    #     return self
