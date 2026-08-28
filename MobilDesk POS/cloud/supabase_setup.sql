-- Kiosko: almacenamiento seguro de sincronizacion entre dispositivos.
-- Ejecute este archivo una sola vez en Supabase > SQL Editor.

create table if not exists public.kiosko_sync_events (
    id uuid primary key,
    negocio_id uuid not null,
    dispositivo_id uuid not null,
    tipo text not null,
    datos jsonb not null,
    creado_en timestamptz not null default now()
);

create index if not exists kiosko_sync_events_negocio_creado_idx
    on public.kiosko_sync_events (negocio_id, creado_en);

alter table public.kiosko_sync_events enable row level security;

-- Permite a los usuarios autenticados utilizar la tabla. Las políticas que
-- siguen mantienen separados los datos de cada negocio.
grant usage on schema public to authenticated;
grant select, insert on table public.kiosko_sync_events to authenticated;

-- Cada cuenta solo puede leer y escribir los datos de su propio negocio.
-- El negocio_id se guarda como metadato de la cuenta al configurarla desde Kiosko.
create policy "Kiosko puede leer sus eventos"
on public.kiosko_sync_events for select
to authenticated
using (negocio_id::text = coalesce(auth.jwt() -> 'user_metadata' ->> 'negocio_id', ''));

create policy "Kiosko puede registrar sus eventos"
on public.kiosko_sync_events for insert
to authenticated
with check (negocio_id::text = coalesce(auth.jwt() -> 'user_metadata' ->> 'negocio_id', ''));

-- No se permiten cambios o borrados remotos: los eventos son un historial.
