-- Corrección para el error: "permission denied for table kiosko_sync_events"
-- Ejecute este archivo una sola vez en Supabase > SQL Editor.

grant usage on schema public to authenticated;
grant select, insert on table public.kiosko_sync_events to authenticated;
