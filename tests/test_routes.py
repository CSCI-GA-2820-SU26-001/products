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
        self.assertIn("Product Demo REST API Service", response.get_data(as_text=True))

    def test_index_json(self):
        """It should return JSON API info when the client explicitly asks for it"""
        response = self.client.get("/", headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "Product REST API Service")

    def test_health(self):
        """It should return a healthy status"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], "OK")

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

    def test_create_product_duplicate_sku(self):
        """It should not create a product with a sku that already exists"""
        new_product = {
            "sku": 1,
            "name": "Test Product",
            "description": "This is a test product.",
            "price": 9.99,
            "image": "http://example.com/image.jpg",
        }
        response = self.client.post("/products", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # attempt to create another product with the same sku
        response = self.client.post("/products", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        data = response.get_json()
        self.assertIn("already exists", data["message"])
        self.assertNotIn("psycopg", data["message"])
        self.assertNotIn("UniqueViolation", data["message"])

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
    # TEST QUERY BY PRICE
    # ----------------------------------------------------------
    def _create_product_with_price(self, sku: int, price: float):
        """Helper to create a Product with a specific price"""
        new_product = {
            "sku": sku,
            "name": f"Product {sku}",
            "description": "A product for price filter tests.",
            "price": price,
            "image": "http://example.com/image.jpg",
        }
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.get_json()

    def test_query_products_by_price(self):
        """It should return only Products priced at or below the given value"""
        self._create_product_with_price(200, 25.00)
        self._create_product_with_price(201, 50.00)
        self._create_product_with_price(202, 75.00)

        response = self.client.get(f"{BASE_URL}?price=50.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        skus = {product["sku"] for product in data}
        self.assertEqual(skus, {200, 201})
        self.assertNotIn(202, skus)
        for product in data:
            self.assertLessEqual(product["price"], 50.00)

    def test_query_products_by_price_no_matches(self):
        """It should return an empty array when every product is priced above the value"""
        self._create_product_with_price(210, 60.00)
        self._create_product_with_price(211, 99.99)

        response = self.client.get(f"{BASE_URL}?price=50.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_query_products_by_price_no_products(self):
        """It should return an empty array when there are no products at all"""
        response = self.client.get(f"{BASE_URL}?price=50.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_query_products_by_price_invalid_value(self):
        """It should return 400 for a non-numeric price query value"""
        response = self.client.get(f"{BASE_URL}?price=not-a-number")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_products_by_min_price(self):
        """It should return only Products priced at or above the given value"""
        self._create_product_with_price(220, 25.00)
        self._create_product_with_price(221, 50.00)
        self._create_product_with_price(222, 75.00)

        response = self.client.get(f"{BASE_URL}?min_price=50.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        skus = {product["sku"] for product in data}
        self.assertEqual(skus, {221, 222})
        self.assertNotIn(220, skus)
        for product in data:
            self.assertGreaterEqual(product["price"], 50.00)

    def test_query_products_by_min_price_no_matches(self):
        """It should return an empty array when every product is priced below min_price"""
        self._create_product_with_price(230, 10.00)
        self._create_product_with_price(231, 20.00)

        response = self.client.get(f"{BASE_URL}?min_price=50.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_query_products_by_min_price_invalid_value(self):
        """It should return 400 for a non-numeric min_price query value"""
        response = self.client.get(f"{BASE_URL}?min_price=not-a-number")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_products_by_price_range(self):
        """It should return only Products within a combined min/max range"""
        self._create_product_with_price(240, 10.00)
        self._create_product_with_price(241, 50.00)
        self._create_product_with_price(242, 90.00)

        response = self.client.get(f"{BASE_URL}?min_price=20.00&price=75.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        skus = {product["sku"] for product in data}
        self.assertEqual(skus, {241})

    def test_query_products_without_price_unchanged(self):
        """It should still return every product when no price query is given"""
        self._create_product_with_price(250, 10.00)
        self._create_product_with_price(251, 90.00)

        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), 2)

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
    # TEST DISCONTINUE ACTION
    # ----------------------------------------------------------
    def test_discontinue_product_success(self):
        """It should discontinue an existing Product"""

        # create a product to discontinue
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # discontinue the product
        new_product = response.get_json()
        logging.debug(new_product)
        sku = new_product["sku"]
        response = self.client.put(f"{BASE_URL}/{sku}/discontinue")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        discontinued_product = response.get_json()
        self.assertEqual(discontinued_product["state"], ProductState.DISCONTINUED.name)

    def test_discontinue_non_existing_product_fail(self):
        """It should not discontinue a non-existing Product"""

        # create a product
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # discontinue a non existing product
        prod = response.get_json()
        logging.debug(prod)
        invalid_sku = prod["sku"] + 1
        response = self.client.put(f"{BASE_URL}/{invalid_sku}/discontinue")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_discontinue_already_discontinued_product_success(self):
        """It should discontinue an existing Product that is already discontinued"""

        # create a product to discontinue
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # discontinue the product
        logging.debug(response.get_json())
        sku = response.get_json()["sku"]
        response = self.client.put(f"{BASE_URL}/{sku}/discontinue")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # discontinue the product again
        response = self.client.put(f"{BASE_URL}/{sku}/discontinue")
        logging.debug(response.get_json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["state"], ProductState.DISCONTINUED.name)

    # ----------------------------------------------------------
    # TEST DEACTIVATE ACTION
    # ----------------------------------------------------------
    def test_deactivate_product_success(self):
        """It should deactivate an existing Product"""

        # create a product to deactivate
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # deactivate the product
        new_product = response.get_json()
        logging.debug(new_product)
        sku = new_product["sku"]
        response = self.client.put(f"{BASE_URL}/{sku}/deactivate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        deactivated_product = response.get_json()
        self.assertEqual(deactivated_product["state"], ProductState.INACTIVE.name)

    def test_deactivate_non_existing_product_fail(self):
        """It should not deactivate a non-existing Product"""

        # create a product
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # deactivate a non existing product
        prod = response.get_json()
        logging.debug(prod)
        invalid_sku = prod["sku"] + 1
        response = self.client.put(f"{BASE_URL}/{invalid_sku}/deactivate")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deactivate_already_inactive_product_success(self):
        """It should deactivate an existing Product that is already activated"""

        # create a product to deactivate
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # deactivate the product
        logging.debug(response.get_json())
        sku = response.get_json()["sku"]
        response = self.client.put(f"{BASE_URL}/{sku}/deactivate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # deactivate the product again
        response = self.client.put(f"{BASE_URL}/{sku}/deactivate")
        logging.debug(response.get_json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["state"], ProductState.INACTIVE.name)

    # ----------------------------------------------------------
    # TEST ACTIVATE ACTION
    # ----------------------------------------------------------
    def test_activate_product_success(self):
        """It should activate an existing Product"""

        # create a product to activate
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # change the product to inactive from its default active state
        response = self.client.put(
            f"{BASE_URL}/{response.get_json()["sku"]}/deactivate"
        )

        # activate the product
        new_product = response.get_json()
        logging.debug(new_product)
        sku = new_product["sku"]
        response = self.client.put(f"{BASE_URL}/{sku}/activate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        activated_product = response.get_json()
        self.assertEqual(activated_product["state"], ProductState.ACTIVE.name)

    def test_activate_non_existing_product_fail(self):
        """It should not activate a non-existing Product"""

        # create a product
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # activate a non existing product
        prod = response.get_json()
        logging.debug(prod)
        invalid_sku = prod["sku"] + 1
        response = self.client.put(f"{BASE_URL}/{invalid_sku}/activate")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_activate_already_activated_product_success(self):
        """It should activate an existing Product that is already activated"""

        # create a product to activate
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # activate the product that is already activated by default
        response = self.client.put(f"{BASE_URL}/{response.get_json()["sku"]}/activate")
        logging.debug(response.get_json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["state"], ProductState.ACTIVE.name)

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
        response = self.client.put(f"{BASE_URL}/{new_product['sku']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["state"], "INACTIVE")

    def test_update_product_with_invalid_state(self):
        """It should not Update a Product with an invalid state value"""
        test_product = self._create_products(1)[0]
        new_product = test_product.serialize()
        new_product["state"] = "NOT_A_REAL_STATE"
        response = self.client.put(f"{BASE_URL}/{new_product['sku']}", json=new_product)
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
