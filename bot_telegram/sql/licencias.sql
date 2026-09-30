-- ============================================================
-- MOBILDESK - Registro de licencias emitidas
-- Ejecutar UNA vez en Supabase > SQL Editor
-- ============================================================

create table if not exists public.mobildesk_licencias (
    id uuid primary key default gen_random_uuid(),
    clave text not null unique,
    machine_id text not null,
    plan text not null,
    plan_nombre text,
    fecha_emision timestamptz not null default now(),
    fecha_expiracion timestamptz,
    estado text not null default 'activa',
    dado_baja_en timestamptz,
    nota text,
    generado_por bigint,
    negocio text
);

create index if not exists idx_mobildesk_licencias_machine
    on public.mobildesk_licencias (machine_id);

create index if not exists idx_mobildesk_licencias_estado
    on public.mobildesk_licencias (estado);

-- Solo el bot escribe/lee. La anon key no debe poder tocar esta tabla.
alter table public.mobildesk_licencias enable row level security;

-- Sin politicas para anon/authenticated: por defecto queda bloqueada.
-- El bot accede con la service_role (que ignora RLS).
