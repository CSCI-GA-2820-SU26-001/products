######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Test cases for Product Model
"""

# pylint: disable=duplicate-code
import os
import logging
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch

# from unittest.mock import patch
# from sqlalchemy.orm import Session
from wsgi import app
from service.models import Product, ProductState, DataValidationError, db
from .factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:pgs3cr3t@postgres:5432/postgres"
)


######################################################################
#  Product   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_repr(self):
        """It should return a human-readable representation of a Product instance"""
        product = ProductFactory()
        self.assertIn("Product", repr(product))

    def test_create_product(self):
        """It should create a Product"""
        product = ProductFactory()
        product.create()
        self.assertIsNotNone(product.sku)

    def test_create_raises_on_db_error(self):
        """It should raise DataValidationError when DB fails on create new product"""
        product = ProductFactory()
        product.create()
        duplicate = ProductFactory()
        duplicate.sku = product.sku  # same SKU triggers unique constraint violation
        self.assertRaises(DataValidationError, duplicate.create)

    # def test_update_raises_on_db_error(self):
    #     """It should raise DataValidationError when DB fails on update"""
    #     product = ProductFactory()
    #     product.create()
    #     with patch.object(Session, "commit", side_effect=Exception("DB error")):
    #         self.assertRaises(DataValidationError, product.update)

    # def test_delete_raises_on_db_error(self):
    #     """It should raise DataValidationError when DB fails on delete"""
    #     product = ProductFactory()
    #     product.create()
    #     with patch.object(Session, "commit", side_effect=Exception("DB error")):
    #         self.assertRaises(DataValidationError, product.delete)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        logging.debug(product)
        product.sku = None
        product.create()
        logging.debug(product)
        self.assertIsNotNone(product.sku)
        # Change it an save it
        product.description = "blah blah"
        original_sku = product.sku
        product.update()
        self.assertEqual(product.sku, original_sku)
        self.assertEqual(product.description, "blah blah")
        # Fetch it back and make sure the sku hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].sku, original_sku)
        self.assertEqual(products[0].description, "blah blah")

    def test_update_no_sku(self):
        """It should not Update a Product with no sku"""
        product = ProductFactory()
        logging.debug(product)
        product.sku = None
        self.assertRaises(DataValidationError, product.update)

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_deserialize_raises_on_missing_key(self):
        """It should raise DataValidationError on missing field"""
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, {"sku": 1})

    def test_deserialize_raises_on_attribute_error(self):
        """It should raise DataValidationError on Attribute Error"""
        product = Product()

        # An object whose __getitem__ raises AttributeError
        class BadData:  # pylint: disable=too-few-public-methods
            """Fake data object that raises AttributeError on key access"""

            def __getitem__(self, key):
                raise AttributeError("Bad Attribute")

        self.assertRaises(DataValidationError, product.deserialize, BadData())

    def test_deserialize_raises_on_type_error(self):
        """It should raise DataValidationError on Type Error"""
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, None)

    def test_read_a_product(self):
        """It should read a Product from the database"""
        product = ProductFactory()
        product.create()
        found = Product.find(product.sku)
        self.assertIsNotNone(found)
        self.assertEqual(found.sku, product.sku)
        self.assertEqual(found.name, product.name)

    def test_find_by_price_matches(self):
        """It should find Products with price less than or equal to given price"""
        cheap_product = ProductFactory()
        cheap_product.price = Decimal("10.00")
        cheap_product.create()

        mid_product = ProductFactory()
        mid_product.price = Decimal("25.00")
        mid_product.create()

        expensive_product = ProductFactory()
        expensive_product.price = Decimal("50.00")
        expensive_product.create()

        products = Product.find_by_price(Decimal("25.00"))

        self.assertEqual(len(products), 2)
        self.assertIn(cheap_product, products)
        self.assertIn(mid_product, products)
        self.assertNotIn(expensive_product, products)

    def test_find_by_price_no_matches(self):
        """It should return no Products when all products have prices above given price"""
        expensive_product = ProductFactory()
        expensive_product.price = Decimal("50.00")
        expensive_product.create()

        products = Product.find_by_price(Decimal("25.00"))

        self.assertEqual(len(products), 0)

    def test_serialize_a_product(self):
        """It should serialize a Product into a dictionary"""
        product = ProductFactory()
        product.create()
        data = product.serialize()
        self.assertIn("sku", data)
        self.assertIn("name", data)
        self.assertIn("description", data)
        self.assertIn("price", data)
        self.assertIn("image", data)
        self.assertIn("state", data)

    def test_deserialize_a_product(self):
        """It should deserialize a Product from a dictionary"""
        product = ProductFactory()
        data = product.serialize()
        new_product = Product()
        new_product.deserialize(data)
        self.assertEqual(new_product.sku, product.sku)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(float(new_product.price), float(product.price))
        self.assertEqual(new_product.image, product.image)
        self.assertEqual(new_product.state, product.state)

    ######################################################################
    #  S T A T E   F I E L D   T E S T   C A S E S
    ######################################################################

    def test_create_product_defaults_to_active_state(self):
        """It should default a new Product's state to ACTIVE when saved without one"""
        # Build the Product directly (bypassing the factory) so the "state"
        # attribute is never touched, allowing the column default to apply.
        product = Product(
            name="Default State Product",
            description="A product created without an explicit state",
            price=Decimal("9.99"),
            image="http://example.com/image.jpg",
        )
        product.create()
        self.assertEqual(product.state, ProductState.ACTIVE)

    def test_deserialize_defaults_state_when_missing(self):
        """It should default state to ACTIVE when deserializing without a state"""
        product = ProductFactory()
        data = product.serialize()
        del data["state"]
        new_product = Product()
        new_product.deserialize(data)
        self.assertEqual(new_product.state, ProductState.ACTIVE)

    def test_deserialize_accepts_each_valid_state(self):
        """It should deserialize a Product with any valid state value"""
        for state in ProductState:
            product = ProductFactory()
            data = product.serialize()
            data["state"] = state.name
            new_product = Product()
            new_product.deserialize(data)
            self.assertEqual(new_product.state, state)

    def test_deserialize_accepts_productstate_instance(self):
        """It should deserialize a Product when state is already a ProductState"""
        product = ProductFactory()
        data = product.serialize()
        data["state"] = ProductState.DISCONTINUED
        new_product = Product()
        new_product.deserialize(data)
        self.assertEqual(new_product.state, ProductState.DISCONTINUED)

    def test_deserialize_accepts_lowercase_state(self):
        """It should deserialize a Product with a lowercase state value"""
        product = ProductFactory()
        data = product.serialize()
        data["state"] = "inactive"
        new_product = Product()
        new_product.deserialize(data)
        self.assertEqual(new_product.state, ProductState.INACTIVE)

    def test_deserialize_raises_on_invalid_state(self):
        """It should raise DataValidationError for an invalid state value"""
        product = ProductFactory()
        data = product.serialize()
        data["state"] = "NOT_A_REAL_STATE"
        new_product = Product()
        self.assertRaises(DataValidationError, new_product.deserialize, data)

    def test_serialize_includes_state(self):
        """It should include the state field when serializing a Product"""
        product = ProductFactory()
        product.state = ProductState.DISCONTINUED
        data = product.serialize()
        self.assertIn("state", data)
        self.assertEqual(data["state"], "DISCONTINUED")


######################################################################
#  T E S T   E X C E P T I O N   H A N D L E R S
######################################################################
class TestExceptionHandlers(TestCase):
    """Product Model Exception Handlers"""

    @patch("service.models.db.session.commit")
    def test_create_exception(self, exception_mock):
        """It should catch a create exception"""
        exception_mock.side_effect = Exception()
        product = ProductFactory()
        self.assertRaises(DataValidationError, product.create)

    @patch("service.models.db.session.commit")
    def test_update_exception(self, exception_mock):
        """It should catch a update exception"""
        exception_mock.side_effect = Exception()
        product = ProductFactory()
        self.assertRaises(DataValidationError, product.update)

    @patch("service.models.db.session.commit")
    def test_delete_exception(self, exception_mock):
        """It should catch a delete exception"""
        exception_mock.side_effect = Exception()
        product = ProductFactory()
        self.assertRaises(DataValidationError, product.delete)
