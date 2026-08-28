ALTER TABLE products
ADD COLUMN codigo_barras TEXT;


ALTER TABLE products
ADD COLUMN marca TEXT;


ALTER TABLE products
ADD COLUMN descripcion TEXT;


ALTER TABLE products
ADD COLUMN unidad TEXT DEFAULT 'unidad';