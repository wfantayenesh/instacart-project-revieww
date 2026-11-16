-- schema.sql
-- This file creates all the tables we need for the Instacart dataset
-- We run this before loading any data

-- aisles table - stores the aisle categories
CREATE TABLE IF NOT EXISTS aisles (
    aisle_id    SMALLINT     NOT NULL,
    aisle_name  VARCHAR(100) NOT NULL
);

-- departments table - stores the department categories
CREATE TABLE IF NOT EXISTS departments (
    department_id   SMALLINT    NOT NULL,
    department_name VARCHAR(50) NOT NULL
);

-- products table - stores all products
CREATE TABLE IF NOT EXISTS products (
    product_id          INTEGER      NOT NULL,
    product_name        VARCHAR(500) NOT NULL,
    aisle_id            SMALLINT     NOT NULL,
    department_id       SMALLINT     NOT NULL,
    product_name_length SMALLINT
);

-- orders table - stores all customer orders
-- days_since_prior_order can be NULL for first orders - that is normal
CREATE TABLE IF NOT EXISTS orders (
    order_id               INTEGER     NOT NULL,
    user_id                INTEGER     NOT NULL,
    eval_set               VARCHAR(10) NOT NULL,
    order_number           SMALLINT    NOT NULL,
    order_dow              SMALLINT    NOT NULL,
    order_hour_of_day      SMALLINT    NOT NULL,
    days_since_prior_order REAL,
    is_first_order         BOOLEAN,
    order_period           VARCHAR(12)
);

-- order_products_train table
CREATE TABLE IF NOT EXISTS order_products_train (
    order_id           INTEGER  NOT NULL,
    product_id         INTEGER  NOT NULL,
    add_to_cart_order  SMALLINT NOT NULL,
    reordered          SMALLINT NOT NULL,
    is_reordered       BOOLEAN
);

-- order_products_prior table - this is the large table with ~32 million rows
CREATE TABLE IF NOT EXISTS order_products_prior (
    order_id           INTEGER  NOT NULL,
    product_id         INTEGER  NOT NULL,
    add_to_cart_order  SMALLINT NOT NULL,
    reordered          SMALLINT NOT NULL,
    is_reordered       BOOLEAN
);
