-- ============================================================
-- MIGRACIÓN 015
-- FIADOS EN USD (FUENTE DE VERDAD) + BS REFLEJADO A TASA ACTUAL
-- ============================================================

ALTER TABLE credit_debts ADD COLUMN total_usd REAL NOT NULL DEFAULT 0;
ALTER TABLE credit_debts ADD COLUMN saldo_usd REAL NOT NULL DEFAULT 0;
ALTER TABLE credit_debts ADD COLUMN tasa_registro REAL;
ALTER TABLE debt_payments ADD COLUMN monto_usd REAL NOT NULL DEFAULT 0;
ALTER TABLE debt_payments ADD COLUMN tasa_pago REAL;

-- Migrar deudas existentes: USD = BS / tasa de la venta original
UPDATE credit_debts
SET total_usd = CASE
        WHEN (SELECT s.tasa_utilizada FROM sales s WHERE s.id = credit_debts.venta_id) > 0
        THEN total_bs / (SELECT s.tasa_utilizada FROM sales s WHERE s.id = credit_debts.venta_id)
        ELSE total_bs END,
    saldo_usd = CASE
        WHEN (SELECT s.tasa_utilizada FROM sales s WHERE s.id = credit_debts.venta_id) > 0
        THEN saldo_bs / (SELECT s.tasa_utilizada FROM sales s WHERE s.id = credit_debts.venta_id)
        ELSE saldo_bs END,
    tasa_registro = (SELECT s.tasa_utilizada FROM sales s WHERE s.id = credit_debts.venta_id);

-- Migrar abonos existentes: USD = BS / tasa de la venta de la deuda
UPDATE debt_payments
SET monto_usd = CASE
        WHEN (SELECT s.tasa_utilizada FROM sales s JOIN credit_debts d ON d.venta_id = s.id WHERE d.id = debt_payments.deuda_id) > 0
        THEN monto_bs / (SELECT s.tasa_utilizada FROM sales s JOIN credit_debts d ON d.venta_id = s.id WHERE d.id = debt_payments.deuda_id)
        ELSE monto_bs END,
    tasa_pago = (SELECT s.tasa_utilizada FROM sales s JOIN credit_debts d ON d.venta_id = s.id WHERE d.id = debt_payments.deuda_id);
