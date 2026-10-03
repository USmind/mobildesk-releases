-- ============================================================================
--  PASO 2 - Registrar tu llave
--
--  Ejecuta ESTE archivo DESPUES de 01_crear_mobildesk_eventos.sql
--
--  La llave se calcula a partir de tu codigo de negocio con esta formula:
--      HMAC-SHA256( "mobildesk-sync-v1" , minusculas(codigo) )
--
--  YA CALCULADA PARA TU CODIGO "MOBIL-6541":
--      ca375b122d7c05d87eff1a0639ec95446861135c8493c5911e520e7cc34bded9
--
--  El UUID del negocio sale de MD5 del codigo en minusculas:
--      b8cc3682-1410-d48c-e5c6-eabf7b18645b
--
--  Si despues quieres usar otro codigo de negocio, cambia los dos valores
--  por los del nuevo codigo.
-- ============================================================================

INSERT INTO public.mobildesk_llaves (negocio_id, llave_hash)
VALUES (
    'b8cc3682-1410-d48c-e5c6-eabf7b18645b',
    'ca375b122d7c05d87eff1a0639ec95446861135c8493c5911e520e7cc34bded9'
)
ON CONFLICT (negocio_id) DO UPDATE SET llave_hash = EXCLUDED.llave_hash;


-- ---------------------------------------------------------------------------
--  COMO CALCULAR LA LLAVE PARA OTRO CODIGO DE NEGOCIO
--
--  Abre PowerShell y ejecuta (cambia el codigo entre comillas):
--
--    $codigo = "MOBIL-6541"
--    $h = [System.Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes("mobildesk-sync-v1"))
--    $llave = -join ($h.ComputeHash([Text.Encoding]::UTF8.GetBytes($codigo.ToLower())) | ForEach-Object { $_.ToString("x2") })
--    $uuid = [System.Guid]::new([byte[]](-join ([Text.Encoding]::UTF8.GetBytes($codigo.ToLower()) | %{ [System.Security.Cryptography.MD5]::HashData($_) })[0..15]))
--    Write-Host "LLLAVE:" $llave
--    Write-Host "UUID :" $uuid
--
--  Despues pegas esos dos valores aqui arriba.
-- ---------------------------------------------------------------------------


-- ---------------------------------------------------------------------------
--  VERIFICACION
--  Debe salir 1 fila con tu negocio.
-- ---------------------------------------------------------------------------
SELECT
    negocio_id,
    llave_hash
FROM public.mobildesk_llaves;

-- Y la tabla de eventos debe seguir vacia y con candado
SELECT
    c.relname AS tabla,
    c.relrowsecurity AS candado_activo,
    (SELECT COUNT(*) FROM public.mobildesk_eventos) AS filas
FROM pg_class c
WHERE c.relname = 'mobildesk_eventos';