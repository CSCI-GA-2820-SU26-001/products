"""
Models for Product

All of the models are stored in this module
"""

import logging
from enum import Enum
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class ProductState(Enum):
    """Enumeration of valid Product states"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISCONTINUED = "DISCONTINUED"


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
    state = db.Column(
        db.Enum(ProductState, name="product_state"),
        nullable=False,
        default=ProductState.ACTIVE,
    )

    def __repr__(self):
        return f"<Product {self.name} sku=[{self.sku}]>"

    def create(self):
        """Creates a Product in the database"""
        logger.info("Creating %s", self.name)
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self) -> None:
        """
        Removes a Product from the database
        """
        logger.info("Deleting %s", self.name)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a Product into a dictionary"""
        return {
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "image": self.image,
            "state": self.state.name if self.state else None,
        }

    def deserialize(self, data):
        """
        Deserializes a Product from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.sku = data["sku"]
            self.name = data["name"]
            self.description = data["description"]
            self.price = data["price"]
            self.image = data["image"]
            # state is optional; defaults to ACTIVE when not provided
            state = data.get("state", ProductState.ACTIVE.name)
            self.state = self._parse_state(state)
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Product: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Product: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    @staticmethod
    def _parse_state(state):
        """Validates and converts a state value into a ProductState

        Args:
            state: a ProductState instance or a string name of one

        Raises:
            DataValidationError: if the state value is not a valid ProductState
        """
        if isinstance(state, ProductState):
            return state
        if isinstance(state, str) and state.upper() in ProductState.__members__:
            return ProductState[state.upper()]
        valid_states = [s.name for s in ProductState]
        raise DataValidationError(
            f"Invalid state: '{state}'. Must be one of {valid_states}"
        )

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all Products in the database"""
        logger.info("Processing all Products")
        return cls.query.all()

    @classmethod
    def find(cls, by_sku):
        """Finds a Product by its SKU"""
        logger.info("Processing lookup for sku %s ...", by_sku)
        return cls.query.session.get(cls, by_sku)

    @classmethod
    def find_by_price(cls, price):
        """Finds all Products with price less than or equal to the given price"""
        logger.info("Processing lookup for products with price <= %s ...", price)
        return cls.query.filter(cls.price <= price).all()

    def update(self) -> None:
        """
        Updates a Product to the database
        """
        logger.info("Saving %s with %s sku", self.name, self.sku)
        if not self.sku:
            raise DataValidationError("Update called with empty sku field")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e
