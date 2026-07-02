"""
Test Factory to make fake objects for testing
"""

import random
from decimal import Decimal

import factory

from service.models import Product, ProductState


class ProductFactory(factory.Factory):
    """Creates fake products that you don't have to feed"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Product

    sku = factory.Sequence(lambda n: n)
    name = factory.Faker("first_name")
    description = factory.Faker("sentence")
    price = factory.LazyAttribute(
        lambda _: Decimal(str(round(random.uniform(0.01, 999999.99), 2)))
    )
    image = factory.Faker("image_url")
    state = factory.Iterator(
        [ProductState.ACTIVE, ProductState.INACTIVE, ProductState.DISCONTINUED]
    )
