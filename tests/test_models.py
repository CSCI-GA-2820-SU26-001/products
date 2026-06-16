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
from unittest import TestCase
from wsgi import app
from service.models import Product, DataValidationError, db
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

    def test_deserialize_raises_on_missing_key(self):
        """It should raise DataValidationError on missing field"""
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, {"sku": 1})

    def test_deserialize_raises_on_attribute_error(self):
        """It should raise DataValidationError on Attribute Error"""
        product = Product()

        # An object whose __getitem__ raises AttributeError
        class BadData:
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

    def test_update_a_product(self):
        """It should update a Product in the database"""
        product = ProductFactory()
        product.create()
        product.name = "Updated Name"
        product.update()
        found = Product.find(product.sku)
        self.assertEqual(found.name, "Updated Name")

    def test_delete_a_product(self):
        """It should delete a Product from the database"""
        product = ProductFactory()
        product.create()
        product.delete()
        self.assertIsNone(Product.find(product.sku))

    def test_list_all_products(self):
        """It should list all Products in the database"""
        ProductFactory().create()
        ProductFactory().create()
        ProductFactory().create()
        products = Product.all()
        self.assertEqual(len(products), 3)

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
