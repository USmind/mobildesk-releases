-- ============================================================================
--  PLANTILLA - Registrar la llave de un negocio NUEVO
--
--  Este archivo es solo el molde. Los valores reales los genera quien compila
--  los programas (tiene la semilla fuera de git) y te los entrega listos para
--  pegar abajo. No inventes valores: si la llave no coincide con la que
--  calcula el programa, ese negocio no sincroniza.
--
--  Lo que va en cada columna:
--    negocio_id : UUID derivado del codigo (MD5 en minusculas, formato UUID)
--    llave_hash : sha256 HEX de la llave HMAC derivada con la semilla real
-- ============================================================================

-- EJEMPLO (no ejecutar tal cual: son valores de muestra, no reales):
--
-- INSERT INTO public.mobildesk_llaves (negocio_id, llave_hash)
-- VALUES (
--     '00000000-0000-0000-0000-000000000000',
--     '0000000000000000000000000000000000000000000000000000000000000000'
-- )
-- ON CONFLICT (negocio_id) DO UPDATE SET llave_hash = EXCLUDED.llave_hash;

-- Verificacion: lista los negocios registrados (sin exponer llaves):
SELECT negocio_id, creado_en FROM public.mobildesk_llaves ORDER BY creado_en;