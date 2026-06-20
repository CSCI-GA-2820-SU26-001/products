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
TestProduct API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from unittest.mock import patch

from wsgi import app
from service.common import status
from service.models import db, Product
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:pgs3cr3t@postgres:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test product",
            )
            new_product = response.get_json()
            test_product.sku = new_product["sku"]
            products.append(test_product)
        return products

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_product(self):
        """
        Test the creation of new product in route /products
        It should create a new product
        """
        new_product = {
            "sku": 1,
            "name": "Test Product",
            "description": "This is a test product.",
            "price": 9.99,
            "image": "http://example.com/image.jpg",
        }
        response = self.client.post("/products", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.get_json()
        logging.debug("JSON results: %s", data)
        self.assertEqual(data["sku"], new_product["sku"])
        self.assertEqual(data["name"], new_product["name"])
        self.assertEqual(data["description"], new_product["description"])
        self.assertEqual(float(data["price"]), new_product["price"])
        self.assertEqual(data["image"], new_product["image"])

    def test_bad_request_missing_field(self):
        """It should not create a product with missing fields"""
        new_product = {
            "sku": 1,
            "name": "Test Product",
            # Missing description, price, and image
        }
        response = self.client.post("/products", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_allowed(self):
        """It should not allow unsupported HTTP methods"""
        response = self.client.put("/products")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_unsupported_media_type(self):
        """It should not allow unsupported media types"""
        new_product = {
            "sku": 1,
            "name": "Test Product",
            "description": "This is a test product.",
            "price": 9.99,
            "image": "http://example.com/image.jpg",
        }
        response = self.client.post("/products", data=str(new_product))
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_product(self):
        """It should retrieve an existing product"""
        new_product = {
            "sku": 42,
            "name": "Get Test Product",
            "description": "A product to retrieve.",
            "price": 5.00,
            "image": "http://example.com/img.jpg",
        }
        self.client.post("/products", json=new_product)
        response = self.client.get("/products/42")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["sku"], 42)

    # ----------------------------------------------------------
    # TEST LIST
    # ----------------------------------------------------------
    def test_get_product_list(self):
        """It should Get a list of Products"""
        self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_not_found(self):
        """It should return 404 for non-existent resources"""
        response = self.client.get("/products/999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unsupported_media_type_wrong_content_type(self):
        """It should reject requests with wrong Content-Type header"""
        response = self.client.post(
            "/products",
            data='{"sku": 1}',
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_internal_server_error(self):
        """It should return 500 for internal server errors"""
        app.config["PROPAGATE_EXCEPTIONS"] = False
        with patch("service.routes.Product") as mock_product:
            mock_product.return_value.deserialize.side_effect = Exception(
                "Unexpected error"
            )
            response = self.client.post(
                "/products",
                json={
                    "sku": 1,
                    "name": "Test Product",
                    "description": "This is a test product.",
                    "price": 9.99,
                    "image": "http://example.com/image.jpg",
                },
                content_type="application/json",
            )
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        app.config["PROPAGATE_EXCEPTIONS"] = True
