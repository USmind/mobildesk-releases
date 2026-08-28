-- ============================================================
-- MIGRACIÓN 014
-- SOPORTE PARA PAGOS MIXTOS Y FRACCIONADOS
-- ============================================================

ALTER TABLE sales ADD COLUMN pagos_detalle TEXT;
