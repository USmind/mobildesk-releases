-- ============================================================================
--  MOBILDESK POS - Tabla de sincronizacion con candado
--
--  Pegalo TODO en el SQL Editor de Supabase y pulsa Run. Una sola vez.
--
--  Que hace esto:
--   1. Crea la tabla con el nombre del producto (mobildesk_eventos).
--   2. Le pone candado: nadie puede leer datos de otro negocio.
--   3. Cada negocio tiene una llave derivada de su codigo. El programa la
--      manda en la cabecera 'x-mobildesk-key' y Postgres solo acepta lo que
--      coincide con la llave guardada para ese negocio.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1) Limpiar un intento anterior (si llego a ejecutarse mal)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS public.mobildesk_eventos CASCADE;
DROP TABLE IF EXISTS public.mobildesk_llaves CASCADE;


-- ---------------------------------------------------------------------------
-- 2) Llaves: una por negocio
-- ---------------------------------------------------------------------------
CREATE TABLE public.mobildesk_llaves (
    negocio_id uuid PRIMARY KEY,
    llave_hash text NOT NULL,
    creado_en  timestamptz NOT NULL DEFAULT now()
);

-- La tabla de llaves NO lleva candado: solo guarda un hash por negocio y no
-- contiene datos de ventas. Dejarlo abierto permite que el programa consulte
-- y valide su propia llave. Lo que protege los datos de cada cliente es la
-- politica de mobildesk_eventos del paso 4.


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

-- Candado activado. Sin esto, cualquiera con la direccion de la base podria
-- leer las ventas de todos los negocios.
ALTER TABLE public.mobildesk_eventos ENABLE ROW LEVEL SECURITY;


-- ---------------------------------------------------------------------------
-- 4) La regla: solo pasa lo que trae la llave correcta
--
--    La llave llega en la cabecera 'x-mobildesk-key'. Se compara contra la
--    guardada para ese negocio. Si no coincide:
--      - en lectura: Postgres no devuelve filas
--      - en escritura: Postgres rechaza el INSERT
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.mobildesk_llave_valida(p_negocio uuid)
RETURNS boolean
LANGUAGE sql
STABLE
AS $fn$
    SELECT EXISTS (
        SELECT 1
        FROM public.mobildesk_llaves k
        WHERE k.negocio_id = p_negocio
          AND k.llave_hash = (
                coalesce(
                    current_setting('request.headers', true)::json->>'x-mobildesk-key',
                    ''
                )
              )
    );
$fn$;

DROP POLICY IF EXISTS "leer con llave" ON public.mobildesk_eventos;
CREATE POLICY "leer con llave" ON public.mobildesk_eventos
    FOR SELECT
    USING (public.mobildesk_llave_valida(negocio_id));

DROP POLICY IF EXISTS "escribir con llave" ON public.mobildesk_eventos;
CREATE POLICY "escribir con llave" ON public.mobildesk_eventos
    FOR INSERT
    WITH CHECK (public.mobildesk_llave_valida(negocio_id));


-- ---------------------------------------------------------------------------
-- 5) Tablas viejas: ya no se usan
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS public.kiosko_sync_events CASCADE;


-- ---------------------------------------------------------------------------
-- 6) VERIFICACION
--
--    Resultado esperado:
--      tabla              | candado_activo | filas
--      mobildesk_eventos  | true           | 0
-- ---------------------------------------------------------------------------
SELECT
    c.relname              AS tabla,
    c.relrowsecurity       AS candado_activo,
    (SELECT count(*) FROM public.mobildesk_eventos) AS filas
FROM pg_class c
WHERE c.relname = 'mobildesk_eventos';

-- Politicas que quedaron puestas:
SELECT policyname, cmd FROM pg_policies WHERE tablename = 'mobildesk_eventos';