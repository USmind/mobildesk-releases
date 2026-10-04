-- ============================================================================
--  PASO 3 - Candado real: rotar la llave y cerrar la lectura de llaves
--
--  Pegalo TODO en el SQL Editor de Supabase y pulsa Run. Una sola vez,
--  DESPUES de instalar los programas nuevos (PC 2.0.39+ / App 1.2.19+).
--
--  Que hace:
--   1. Activa pgcrypto para comparar hashes dentro de Postgres.
--   2. La funcion de validacion pasa a SECURITY DEFINER: lee las llaves
--      aunque nadie mas pueda, y compara sha256, no la llave directa.
--   3. Quita TODO permiso sobre mobildesk_llaves: ni lectura. La llave
--      deja de estar expuesta aunque alguien tenga la direccion de la base.
--   4. Rota la llave del negocio a la nueva semilla (fuera de git).
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- 1) Funcion con privilegios propios + comparacion por hash
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.mobildesk_llave_valida(p_negocio uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $fn$
    SELECT EXISTS (
        SELECT 1
        FROM public.mobildesk_llaves k
        WHERE k.negocio_id = p_negocio
          AND k.llave_hash = encode(
                digest(
                  coalesce(
                    current_setting('request.headers', true)::json->>'x-mobildesk-key',
                    ''
                  ),
                  'sha256'
                ),
                'hex'
              )
    );
$fn$;

-- ---------------------------------------------------------------------------
-- 2) Nadie lee ni toca la tabla de llaves, salvo la funcion de arriba
-- ---------------------------------------------------------------------------
REVOKE ALL ON public.mobildesk_llaves FROM anon, authenticated, PUBLIC;

-- Los eventos siguen igual: lectura+escritura solo con llave valida.
-- (Se reafirman por si algun paso anterior los dejo abiertos.)
GRANT SELECT, INSERT ON public.mobildesk_eventos TO anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3) Rotar la llave del negocio a la semilla nueva (fuera de git)
--    negocio: MOBIL-6541 -> b8cc3682-1410-d48c-e5c6-eabf7b18645b
--    valor: sha256 de la llave derivada con la semilla real
-- ---------------------------------------------------------------------------
INSERT INTO public.mobildesk_llaves (negocio_id, llave_hash)
VALUES (
    'b8cc3682-1410-d48c-e5c6-eabf7b18645b',
    '3dfd61e339e771e63304612335279178199b9cb14999294d7ce3f0f2a5680f12'
)
ON CONFLICT (negocio_id) DO UPDATE SET llave_hash = EXCLUDED.llave_hash;

-- ---------------------------------------------------------------------------
-- 4) VERIFICACION
-- ---------------------------------------------------------------------------
-- La llave vieja (ca375b12...) ya NO debe validar. Comprueba que la funcion
-- existe y es definer:
SELECT
    p.proname AS funcion,
    p.prosecdef AS es_definer
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname = 'mobildesk_llave_valida';

-- Debe salir 1 fila con tu negocio:
SELECT negocio_id FROM public.mobildesk_llaves;

-- Tabla de eventos con candado y sus politicas:
SELECT policyname, cmd FROM pg_policies WHERE tablename = 'mobildesk_eventos';