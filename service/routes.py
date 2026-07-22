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

from decimal import Decimal, InvalidOperation
from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from flask_restx import Api, Resource, fields
from service.common import status
from service.models import Product, ProductState  # HTTP Status Codes

api = Api(
    app,
    version="1.0.0",
    title="Product REST API Service",
    description="This is a sample server Product manager server.",
    default="products",
    default_label="Product operations",
    doc="/apidocs",  # default also could use doc='/apidocs/'
    prefix="/api",
)

ns = api.default_namespace

product_model = api.model(
    "Product",
    {
        "sku": fields.Integer(readonly=True, description="Unique product identifier"),
        "name": fields.String(required=True, description="Product name"),
        "description": fields.String(required=True, description="Product description"),
        "price": fields.Float(required=True, description="Product price"),
        "image": fields.String(required=True, description="Product image URL"),
        "state": fields.String(
            description="Product state: ACTIVE, INACTIVE, or DISCONTINUED"
        ),
    },
)


######################################################################
# HEALTH CHECK
######################################################################
@app.route("/health")
def health_check():
    """Health endpoint for Kubernetes liveness/readiness probes"""
    return jsonify(status="OK"), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Base URL for our service

    Serves the HTML UI by default (browsers, plain requests with no
    Accept header) and the JSON API info only when the client
    explicitly asks for JSON without also accepting HTML.

    This route lives outside the /api namespace entirely, belongs
    to the UI, not the REST API.
    """
    accept_header = request.headers.get("Accept", "")
    if "application/json" in accept_header and "text/html" not in accept_header:
        return (
            jsonify(
                name="Product REST API Service",
                version="1.0",
                paths=url_for("products", _external=True),
            ),
            status.HTTP_200_OK,
        )
    return app.send_static_file("index.html")


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
#  PATH: /products
######################################################################
@ns.route("/products", endpoint="products")
class ProductCollection(Resource):
    """Handles interactions with the collection of Products"""

    # ------------------------------------------------------------
    # LIST / QUERY ALL PRODUCTS
    # ------------------------------------------------------------
    @ns.marshal_with(product_model)
    def get(self):
        """Returns all of the Products

        Optionally filters the list with query strings:
          - ?price=<value>      Products priced at or below the given value
          - ?min_price=<value>  Products priced at or above the given value
        Both may be combined for a range. Without either query param, behavior
        is unchanged.
        """
        app.logger.info("Request for product list")

        max_price = _parse_price_query_arg("price")
        min_price = _parse_price_query_arg("min_price")

        if (
            min_price is not None
            and max_price is not None
            and Decimal(min_price) > Decimal(max_price)
        ):
            abort(
                status.HTTP_400_BAD_REQUEST,
                "min_price cannot be greater than max price.",
            )

        if max_price is not None or min_price is not None:
            app.logger.info(
                "Filtering products with price range min=%s, max=%s",
                min_price,
                max_price,
            )
            products = Product.find_by_price_range(
                min_price=min_price, max_price=max_price
            )
        else:
            # Return all of the Products
            products = Product.all()

        results = [product.serialize() for product in products]
        app.logger.info("Returning %d product", len(results))
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------
    # CREATE A NEW PRODUCT
    # ------------------------------------------------------------
    @ns.expect(product_model, validate=True)
    @ns.marshal_with(product_model, code=status.HTTP_201_CREATED)
    def post(self):
        """Creates a new Product

        Accept JSON format to create a new product. All fields are required
        except "state", which defaults to "ACTIVE" if not provided.
        Sample :
            {
                "sku": 1001,
                "name": "Test Product",
                "description": "A test product",
                "price": 19.99,
                "image": "http://example.com/image.jpg",
                "state": "ACTIVE"
            }
        """
        app.logger.info("Request to create a Product")
        product = Product()
        product.deserialize(request.get_json())

        if Product.find(product.sku):
            abort(
                status.HTTP_409_CONFLICT,
                f"Product with sku '{product.sku}' already exists.",
            )

        product.create()
        location_url = url_for("product", sku=product.sku, _external=True)
        return (
            product.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


######################################################################
#  PATH: /products/<int:sku>
######################################################################
@ns.route("/products/<int:sku>", endpoint="product")
class ProductResource(Resource):
    """Handles interactions with a single Product"""

    # ------------------------------------------------------------
    # READ A PRODUCT
    # ------------------------------------------------------------
    @ns.marshal_with(product_model)
    def get(self, sku):
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
        return product.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------
    # UPDATE AN EXISTING PRODUCT
    # ------------------------------------------------------------
    @ns.expect(product_model, validate=True)
    @ns.marshal_with(product_model)
    def put(self, sku):
        """
        Update a Product

        This endpoint will update a Product based the body that is posted
        """
        app.logger.info("Request to Update a Product with sku [%s]", sku)

        # Attempt to find the Product and abort if not found
        product = Product.find(sku)
        if not product:
            abort(status.HTTP_404_NOT_FOUND, f"Product with id '{sku}' was not found.")

        # Update the Product with the new data
        data = request.get_json()
        app.logger.info("Processing: %s", data)

        product.deserialize(data)

        # Save the updates to the database
        product.update()

        app.logger.info("Product with SKU: %d updated.", product.sku)
        return product.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------
    # DELETE A PRODUCT
    # ------------------------------------------------------------
    @ns.response(status.HTTP_204_NO_CONTENT, "Product deleted")
    def delete(self, sku):
        """
        Delete a Product

        This endpoint will delete a Product based on the sku specified in the path
        """
        app.logger.info("Request to Delete a product with sku [%s]", sku)

        # Delete the Product if it exists
        product = Product.find(sku)
        if product:
            app.logger.info("Product with sku: %d found.", product.sku)
            product.delete()

        app.logger.info("Product with sku: %d delete complete.", sku)
        return {}, status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /products/<int:sku>/activate
######################################################################
@ns.route("/products/<int:sku>/activate", endpoint="activate")
class ActivateResource(Resource):
    """Activate action on a Product"""

    @ns.marshal_with(product_model)
    def put(self, sku):
        """
        Activate a Product

        This endpoint will Activate a Product with the provided sku
        """
        app.logger.info("Request to Activate Product with sku [%s]", sku)

        product = Product.find(sku)
        if not product:
            abort(status.HTTP_404_NOT_FOUND, f"Product with sku '{sku}' was not found.")

        product.state = ProductState.ACTIVE
        product.update()

        app.logger.info("Product with SKU: %d activated.", product.sku)
        return product.serialize(), status.HTTP_200_OK


######################################################################
#  PATH: /products/<int:sku>/deactivate
######################################################################
@ns.route("/products/<int:sku>/deactivate", endpoint="deactivate")
class DeactivateResource(Resource):
    """Deactivate action on a Product"""

    @ns.marshal_with(product_model)
    def put(self, sku):
        """
        Deactivate a Product

        This endpoint will Deactivate a Product with the provided sku
        """
        app.logger.info("Request to Deactivate Product with sku [%s]", sku)

        product = Product.find(sku)
        if not product:
            abort(status.HTTP_404_NOT_FOUND, f"Product with sku '{sku}' was not found.")

        product.state = ProductState.INACTIVE
        product.update()

        app.logger.info("Product with SKU: %d deactivated.", product.sku)
        return product.serialize(), status.HTTP_200_OK


######################################################################
#  PATH: /products/<int:sku>/discontinue
######################################################################
@ns.route("/products/<int:sku>/discontinue", endpoint="discontinue")
class DiscontinueResource(Resource):
    """Discontinue action on a Product"""

    @ns.marshal_with(product_model)
    def put(self, sku):
        """
        Discontinue a Product

        This endpoint will Discontinue a Product with the provided sku
        """
        app.logger.info("Request to Discontinue a Product with sku [%s]", sku)

        product = Product.find(sku)
        if not product:
            abort(status.HTTP_404_NOT_FOUND, f"Product with sku '{sku}' was not found.")

        product.state = ProductState.DISCONTINUED
        product.update()

        app.logger.info("Product with SKU: %d discontinued.", product.sku)
        return product.serialize(), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def _parse_price_query_arg(arg_name):
    """Reads a price-like query string argument and parses it as a Decimal

    Aborts with 400 Bad Request if the value is present but not a valid
    number. Returns None if the argument was not supplied at all.
    """
    value = request.args.get(arg_name)
    if value is None:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        abort(
            status.HTTP_400_BAD_REQUEST,
            f"Invalid {arg_name} value: '{value}'. Must be a number.",
        )
        return None  # pragma: no cover - abort() always raises
