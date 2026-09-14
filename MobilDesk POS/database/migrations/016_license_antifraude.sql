-- Migración 016: Antifraude de licencias (detección de reloj atrasado).
-- Guarda la última apertura real del sistema. Si al abrir la fecha del
-- equipo es anterior a la última apertura registrada, el sistema lo
-- detecta (reloj manipulado para extender el demo) y se bloquea hasta
-- corregir la fecha. NULL = sin registro previo (se crea al abrir).
ALTER TABLE system_license ADD COLUMN ultima_apertura TEXT;
