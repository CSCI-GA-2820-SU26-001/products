# DevOps Products 

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

## Overview

A REST API for managing products as part of an ecommerce application. It stores each product along side a series of descriptors for it: a name, description, price, an associated image and a sku code. It can be used to create new products and read, update, list or delete existing ones.

-------

The Products service utilizes:  
- Python   
- Flask  
- PostgreSQL 

And runs on Docker



## Setup

Clone the repo: `git clone https://github.com/CSCI-GA-2820-SU26-001/products`

Open the repo in a container

Run the service: `make run`

Access the local service: `http://localhost:8080/` 

## Endpoint Info


### Create a Product

```
POST /products

Request:
{
  "description": "Example Description",
  "image": "https://dummyimage.com/623x359",
  "name": "Example Name",
  "price": 15.25,
  "sku": 30
}

201 CREATED

{
  "description": "Example Description",
  "image": "https://dummyimage.com/623x359",
  "name": "Example Name",
  "price": 15.25,
  "sku": 30
}

```


### Display a Product

```
GET /products/<sku>

200 OK

{
  "description": "Example description",
  "image": "https://dummyimage.com/623x359",
  "name": "Example Name",
  "price": 78875.51,
  "sku": 28
}

OR

404 NOT FOUND

{
  "error": "Not Found",
  "message": "404 Not Found: Product with sku '999' was not found.",
  "status": 404
}

```

### Display all Products

```
GET /products

200 OK

[
  {
    "description": "Example description",
    "image": "https://dummyimage.com/623x359",
    "name": "Example Name",
    "price": 78875.51,
    "sku": 28
  },
  {
    "description": "Example description two",
    "image": "https://dummyimage2.com/623x359",
    "name": "Example Name Two",
    "price": 68875.51,
    "sku": 29
  }
]
```

### Delete a Product

```
DELETE /products/<sku>

204 NO CONTENT
```


### Update a Product

```
PUT /products/<sku>

Request:
{
  "description": "Updated Description",
  "image": "https://dummyimage.com/623x359",
  "name": "Updated Name",
  "price": 7.5,
  "sku": 30
}

200 OK

{
  "description": "Updated Description",
  "image": "https://dummyimage.com/623x359",
  "name": "Updated Name",
  "price": 7.5,
  "sku": 30
}

OR

404 NOT FOUND

{
  "error": "Not Found",
  "message": "404 Not Found: Product with id '999' was not found.",
  "status": 404
}

```

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
