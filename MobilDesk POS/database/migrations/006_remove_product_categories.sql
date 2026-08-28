-- Categories are no longer part of the product workflow.
-- The legacy table is kept for historical compatibility.
UPDATE products SET categoria_id = NULL;
