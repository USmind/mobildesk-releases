-- ============================================================================
--  MOBILDESK POS - Tabla de sincronizacion con candado
--
--  Pegalo TODO en el SQL Editor de Supabase y pulsa Run. Una sola vez.
--
--  Que hace esto:
--   1. Crea la tabla con el nombre del producto (mobildesk_eventos).
--   2. Le pone candado: nadie puede leer datos de otro negocio.
--   3. La llave de cada negocio se guarda hasheada. El programa manda el
--      hash en la cabecera x-mobildesk-key y Postgres solo acepta lo que
--      coincide con el hash almacenado.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1) Limpiar intento anterior (si lo ejecutaste mal antes)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS public.mobildesk_eventos CASCADE;
DROP TABLE IF EXISTS public.mobildesk_llaves CASCADE;


-- ---------------------------------------------------------------------------
-- 2) Llaves: un hash por negocio
-- ---------------------------------------------------------------------------
CREATE TABLE public.mobildesk_llaves (
    negocio_id uuid PRIMARY KEY,
    llave_hash text NOT NULL,
    creado_en  timestamptz NOT NULL DEFAULT now()
);

-- El codigo publico se usa para consultar la llave propia.
ALTER TABLE public.mobildesk_llaves ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "leer propia llave" ON public.mobildesk_llaves;
CREATE POLICY "leer propia llave" ON public.mobildesk_llaves
    FOR SELECT
    USING (true);


-- ---------------------------------------------------------------------------
-- 3) Eventos de sincronizacion
-- ---------------------------------------------------------------------------
CREATE TABLE public.mobildesk_eventos (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    negocio_id     uuid NOT NULL,
    dispositivo_id uuid,
    tipo           text NOT NULL,
    datos          jsonb NOT NULL DEFAULT '{}'::jsonb,
    creado_en      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_mobildesk_eventos_negocio
    ON public.mobildesk_eventos (negocio_id, creado_en);

-- Candado activado: sin esto, cualquiera con la direccion de la base
-- podria leer las ventas de todos los negocios.
ALTER TABLE public.mobildesk_eventos ENABLE ROW LEVEL SECURITY;


-- ---------------------------------------------------------------------------
-- 4) La regla: solo pasa lo que trae la llave correcta
--
--    La llave llega en la cabecera 'x-mobildesk-key'. Se compara contra el
--    hash guardado para ese negocio. Si no coincide, Postgres no devuelve
--    nada (lectura) o rechaza la escritura.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.mobildesk_llave_valida(p_negocio uuid)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.mobildesk_llaves k
        WHERE k.negocio_id = p_negocio
          AND k.llave_hash = (
                current_setting('request.headers', true)::json->>'x-mobildesk-key'
              )
    );
$$;

DROP POLICY IF EXISTS "leer con llave" ON public.mobildesk_eventos;
CREATE POLICY "leer con llave" ON public.mobildesk_eventos
    FOR SELECT
    USING (public.mobildesk_llave_valida(negocio_id));

DROP POLICY IF EXISTS "escribir con llave" ON public.mobildesk_eventos;
CREATE POLICY "escribir con llave" ON public.mobildesk_eventos
    FOR INSERT
    WITH CHECK (public.mobildesk_llave_valida(negocio_id));


-- ---------------------------------------------------------------------------
-- 5) Verificacion
--    Debe mostrar:  mobildesk_eventos | true   | 0
-- ---------------------------------------------------------------------------
SELECT
    c.relname   AS tabla,
    c.relrowsecurity AS candado_activo,
    (SELECT COUNT(*) FROM public.mobildesk_eventos) AS filas
FROM pg_class c
WHERE c.relname = 'mobildesk_eventos';


-- ---------------------------------------------------------------------------
-- 6) Tablas viejas: ya no se usan
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS public.kiosko_sync_events CASCADE;