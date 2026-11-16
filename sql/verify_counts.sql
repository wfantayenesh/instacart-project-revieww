-- verify_counts.sql
-- Run SELECT COUNT(*) on all tables to verify the data was loaded correctly

SELECT 'aisles' AS table_name, COUNT(*) AS row_count FROM aisles;

SELECT 'departments' AS table_name, COUNT(*) AS row_count FROM departments;

SELECT 'products' AS table_name, COUNT(*) AS row_count FROM products;

SELECT 'orders' AS table_name, COUNT(*) AS row_count FROM orders;

SELECT 'order_products_train' AS table_name, COUNT(*) AS row_count FROM order_products_train;

SELECT 'order_products_prior' AS table_name, COUNT(*) AS row_count FROM order_products_prior;

-- summary - all tables in one result
SELECT table_name, row_count FROM (
    SELECT 'aisles'               AS table_name, COUNT(*) AS row_count FROM aisles
    UNION ALL
    SELECT 'departments',                         COUNT(*) FROM departments
    UNION ALL
    SELECT 'products',                            COUNT(*) FROM products
    UNION ALL
    SELECT 'orders',                              COUNT(*) FROM orders
    UNION ALL
    SELECT 'order_products_train',                COUNT(*) FROM order_products_train
    UNION ALL
    SELECT 'order_products_prior',                COUNT(*) FROM order_products_prior
) AS counts
ORDER BY table_name;
