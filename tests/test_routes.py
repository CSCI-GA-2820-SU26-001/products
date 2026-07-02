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
# from itertools import product
import os
import logging
from unittest import TestCase
from unittest.mock import patch

from wsgi import app
from service.common import status
from service.models import db, Product, ProductState
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
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "Product REST API Service")

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
        self.assertEqual(data["state"], "ACTIVE")

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
        """
        It should retrieve an existing product in route /productsGET /products/{sku}
        """
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
        self.assertIn("state", data)
        self.assertEqual(data["state"], "ACTIVE")

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

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------
    def test_delete_product(self):
        """It should Delete a Product"""
        test_product = self._create_products(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_product.sku}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_product.sku}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existing_product(self):
        """It should Delete a Product even if it doesn't exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

    def test_get_empty_product_list(self):
        """It should Get an empty list of Products when there are none"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 0)

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------
    def test_update_product_success(self):
        """It should Update an existing Product"""
        # create a product to update
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the product
        new_product = response.get_json()
        logging.debug(new_product)
        new_product["name"] = "Tara"
        response = self.client.put(f"{BASE_URL}/{new_product['sku']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["name"], "Tara")

    def test_update_product_does_not_exist(self):
        """It should not Update a non-existing Product"""
        # create a product to update
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update a non-existing product (with different sku)
        new_product = response.get_json()
        logging.debug(new_product)
        new_product["sku"] = new_product["sku"] - 1
        response = self.client.put(f"{BASE_URL}/{new_product['sku']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_with_missing_info(self):
        """It should not Update a Product with missing field in payload"""
        # create a product to update
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the created product without a required field (name)
        new_product = response.get_json()
        logging.debug(new_product)
        new_product.pop("name")
        response = self.client.put(f"{BASE_URL}/{new_product['sku']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_product_with_missing_sku(self):
        """It should not Update a Product without sku"""
        # create a product to update
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the created product without an sku
        new_product = response.get_json()
        logging.debug(new_product)
        temp = new_product["sku"]
        new_product.pop("sku")
        response = self.client.put(f"{BASE_URL}/{temp}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_product_with_incorrect_info(self):
        """It should not Update a Product with incorrect field in payload"""
        # create a product to update
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the created product with a price more than 10 digits
        new_product = response.get_json()
        logging.debug(new_product)
        new_product["price"] = 11111111111111111111.123
        response = self.client.put(f"{BASE_URL}/{new_product['sku']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ----------------------------------------------------------
    # TEST STATE FIELD
    # ----------------------------------------------------------
    def test_create_product_with_valid_state(self):
        """It should create a Product with a specified valid state"""
        new_product = {
            "sku": 100,
            "name": "Stateful Product",
            "description": "A product with an explicit state.",
            "price": 9.99,
            "image": "http://example.com/image.jpg",
            "state": "DISCONTINUED",
        }
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.get_json()
        self.assertEqual(data["state"], "DISCONTINUED")

    def test_create_product_with_invalid_state(self):
        """It should not create a Product with an invalid state value"""
        new_product = {
            "sku": 101,
            "name": "Bad State Product",
            "description": "A product with an invalid state.",
            "price": 9.99,
            "image": "http://example.com/image.jpg",
            "state": "NOT_A_REAL_STATE",
        }
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("message", data)
        self.assertIn("state", data["message"].lower())

    def test_update_product_with_valid_state(self):
        """It should Update an existing Product with a new valid state"""
        test_product = self._create_products(1)[0]
        new_product = test_product.serialize()
        new_product["state"] = "INACTIVE"
        response = self.client.put(
            f"{BASE_URL}/{new_product['sku']}", json=new_product
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["state"], "INACTIVE")

    def test_update_product_with_invalid_state(self):
        """It should not Update a Product with an invalid state value"""
        test_product = self._create_products(1)[0]
        new_product = test_product.serialize()
        new_product["state"] = "NOT_A_REAL_STATE"
        response = self.client.put(
            f"{BASE_URL}/{new_product['sku']}", json=new_product
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_without_state_defaults_to_active(self):
        """It should default a Product's state to ACTIVE when not provided"""
        new_product = {
            "sku": 102,
            "name": "No State Product",
            "description": "A product without a state field.",
            "price": 9.99,
            "image": "http://example.com/image.jpg",
        }
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.get_json()
        self.assertEqual(data["state"], ProductState.ACTIVE.name)

    def test_not_found(self):
        """It should return 404 for non-existent resources"""
        response = self.client.get("/products/999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_product_not_found_zero_sku(self):
        """It should return 404 when retrieving a product with SKU that does not exist"""
        response = self.client.get("/products/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("0", str(data))

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
