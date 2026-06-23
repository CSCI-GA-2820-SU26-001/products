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
Product Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Product
"""

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.common import status
from service.models import Product  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


@app.route("/products", methods=["POST"])
def create_product():
    """Creates a new Product

    Accept JSON format to create a new product. All fields are required.
    Sample :
        {
            "sku": 1001,
            "name": "Test Product",
            "description": "A test product",
            "price": 19.99,
            "image": "http://example.com/image.jpg"
        }
    """
    app.logger.info("Request to create a Product")
    check_content_type("application/json")
    product = Product()
    product.deserialize(request.get_json())
    product.create()
    location_url = url_for("get_product", sku=product.sku, _external=True)
    return (
        jsonify(product.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# READ A PRODUCT
######################################################################
@app.route("/products/<int:sku>", methods=["GET"])
def get_product(sku):
    """Retrieves a single Product
    Accept parameters: SKU<integer>
    Returns: product object in JSON format
            200 OK on success
            404 Not Found if product does not exist
    """
    app.logger.info("Request for product with sku: %s", sku)
    product = Product.find(sku)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with sku '{sku}' was not found.")
    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# LIST ALL PRODUCTS
######################################################################
@app.route("/products", methods=["GET"])
def list_products():
    """Returns all of the Products"""
    app.logger.info("Request for product list")

    # Return all of the Products
    products = Product.all()

    results = [product.serialize() for product in products]
    app.logger.info("Returning %d product", len(results))
    return jsonify(results), status.HTTP_200_OK


######################################################################
# DELETE A PRODUCT
######################################################################
@app.route("/products/<int:by_sku>", methods=["DELETE"])
def delete_products(by_sku):
    """
    Delete a Product

    This endpoint will delete a Product based on the sku specified in the path
    """
    app.logger.info("Request to Delete a product with siu [%s]", by_sku)

    # Delete the Product if it exists
    product = Product.find(by_sku)
    if product:
        app.logger.info("Product with sku: %d found.", product.sku)
        product.delete()

    app.logger.info("Product with sku: %d delete complete.", by_sku)
    return {}, status.HTTP_204_NO_CONTENT


######################################################################
# UPDATE AN EXISTING PRODUCT
######################################################################
@app.route("/products/<int:by_sku>", methods=["PUT"])
def update_products(by_sku):
    """
    Update a Product

    This endpoint will update a Product based the body that is posted
    """
    app.logger.info("Request to Update a Product with sku [%s]", by_sku)
    check_content_type("application/json")

    # Attempt to find the Product and abort if not found
    product = Product.find(by_sku)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, f"Product with id '{by_sku}' was not found.")

    # Update the Product with the new data
    data = request.get_json()
    app.logger.info("Processing: %s", data)

    product.deserialize(data)

    # Save the updates to the database
    product.update()

    app.logger.info("Product with SKU: %d updated.", product.sku)
    return product.serialize(), status.HTTP_200_OK

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )
