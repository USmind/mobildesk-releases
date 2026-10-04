-- ============================================================================
--  PASO 4 - Permitir la limpieza automatica de eventos viejos
--
--  Pegalo en el SQL Editor de Supabase y pulsa Run. Una sola vez.
--
--  Que hace:
--   1. Da permiso de borrado (solo con la politica de abajo).
--   2. Politica "borrar con llave": cada negocio solo puede borrar SUS
--      propios eventos. Sin la llave correcta, el DELETE se rechaza.
--
--  Sin esto, la limpieza que hace la PC falla en silencio y la nube crece
--  sin fin. Con esto, la PC borra sola ventas/movimientos/abonos/tasas de
--  mas de 60 dias. El catalogo (productos, config) no se toca nunca.
-- ============================================================================

GRANT DELETE ON public.mobildesk_eventos TO anon, authenticated;

DROP POLICY IF EXISTS "borrar con llave" ON public.mobildesk_eventos;
CREATE POLICY "borrar con llave" ON public.mobildesk_eventos
    FOR DELETE
    USING (public.mobildesk_llave_valida(negocio_id));

-- ---------------------------------------------------------------------------
-- VERIFICACION: deben salir 3 politicas (leer, escribir, borrar)
-- ---------------------------------------------------------------------------
SELECT policyname, cmd
FROM pg_policies
WHERE tablename = 'mobildesk_eventos'
ORDER BY cmd;