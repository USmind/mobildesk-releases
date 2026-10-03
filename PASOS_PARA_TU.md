# PASO A PASO - Que hacer manana

Todo son 2 archivos SQL y la instalacion del programa. unos 10 minutos.

El orden importa: PRIMERO la base, DESPUES el programa.

---

## ANTES DE EMPEZAR

Tener a la mano:
- El proyecto de Supabase abierto (es donde ya worked antes, el que termina en
  atxeuhqhariymdqsbmpd)
- El explorador de archivos

---

# PASO 1 - Copiar el primer archivo SQL

## 1.1 Abrir la carpeta sql en GitHub

Pega esto en el navegador y dale Enter:

    https://github.com/USmind/mobildesk-releases/tree/main/sql

## 1.2 Entrar al archivo 01

En la lista, haz clic en:

    01_crear_mobildesk_eventos.sql

## 1.3 Copiar TODO el texto

Arriba a la derecha hay un boton que dice **Raw**. Dale clic.
Se abre el texto solo en una pestana.

Selecciona TODO (Control + A) y copialo (Control + C).

Cierra esa pestana. Ya lo tienes copiado.

---

# PASO 2 - Pegar y ejecutar en Supabase

## 2.1 Abrir el editor SQL

En Supabase, en la barra lateral izquierda, haz clic en el icono de un
**cuaderno o documento** (SQL Editor).

## 2.2 Crear una consulta nueva

Te aparece un boton **"+ New query"** o **"New SQL query"**. dale clic.

## 2.3 Pegar

Haz clic dentro del area de texto grande y pega:

    Control + V

## 2.4 Ejecutar

Hay un boton verde que dice **Run**. dale clic.

Espera unos segundos.

## 2.5 QUE TIENES QUE VER

Abajo sale una pestana llamada **Results** o **Result**. Debe mostrar una
tabla parecida a esta:

    tabla              | candado_activo | filas
    -------------------+----------------+-------
    mobildesk_eventos  | true           | 0

Tambien salen 2 lineas con los nombres de las politicas:

    leer con llave     | SELECT
    escribir con llave | INSERT

**Si ves eso, el Paso 2 esta bien. Pasa al Paso 3.**

**Si sale un error en rojo**, no sigas. Copia aqui el texto del error y
me lo mandas. No continues todavia.

---

# PASO 3 - Registrar tu llave

## 3.1 Crear otra consulta nueva

Vuelve a crear una consulta nueva (el boton "+").

## 3.2 Copiar el segundo archivo

Vuelve al navegador y abre:

    https://github.com/USmind/mobildesk-releases/blob/main/sql/02_registrar_llave.sql

Haz clic en **Raw**, selecciona todo (Control + A), copia (Control + C).

## 3.3 Pegar y ejecutar

Pega en el editor (Control + V) y dale **Run**.

## 3.4 QUE TIENES QUE VER

Debes ver tu negocio:

    negocio_id                                | llave_hash
    -----------------------------------------+-----
    b8cc3682-1410-d48c-e5c6-eabf7b18645b      | ca375b12...

Y la tabla de eventos:

    tabla              | candado_activo | filas
    -------------------+----------------+-------
    mobildesk_eventos  | true           | 0

**Si aparece tu negocio con esos datos, ya terminaste la parte de la base.**

---

# PASO 4 (opcional) - Borrar las licencias de prueba

Solo si quieres dejar las licencias limpias.

Crea otra consulta nueva y pega SOLO esto:

    DELETE FROM public.mobildesk_licencias;

Dale **Run**.

---

# PASO 5 - Instalar el programa

## 5.1 Descargar la PC

Abre:

    https://github.com/USmind/mobildesk-releases/releases/tag/v2.0.38

Baja el archivo:

    Instalar-MobilDesk-v2.0.38.exe

## 5.2 Instalar

- Cierra el programa viejo si lo tiene abierto.
- Doble clic en el instalador.
- Espera a que termine.
- Si Windows pregunta si permitir, di **Si**.

---

# PASO 6 - Empezar de cero

## 6.1 Primer inicio

Al abrir el programa por primera vez te aparece la pantalla
**Configuracion Inicial**. Ahi escribes:

- **Nombre del negocio:** el que quieras (ej: "Mi Bodega")
- **Usuario:** el que quieras (ej: "admin")
- **Contrasena:** la que quieras, no se te va a olvidar porque tu la pones

## 6.2 Activar la licencia

El programa te va a pedir la licencia. Activala como siempre.

---

# PASO 7 - Conectar el celular

## 7.1 En la computadora

Abre el modulo **Sincronizacion**. Ahi aparece tu **Codigo de Negocio**.

Si ya tenias uno antes, sera el mismo (MOBIL-6541). Si no, el programa te
genera uno nuevo. **Anotalo.**

## 7.2 En el celular

Instala la app 1.2.17:

    https://github.com/USmind/mobildesk-releases/releases/tag/v2.0.38

Baja `MobilDesk-v1.2.17.apk`.

Abre la app, escribe el **mismo codigo** que dice en la computadora y
dale **Conectar**.

## 7.3 Probar

Agrega un producto de prueba en el celular. En unos segundos deberia
aparecer tambien en la computadora.

---

# SI ALGO SALE MAL

## "Could not find the table"
Aun no se creo la tabla. Vuelve al Paso 2.

## "Sin conexion a Internet"
Mismo caso que el anterior. Revisa que los 2 SQL se ejecutaron.

## El celular no trae los productos
- Revisa que el codigo sea IGUAL en los dos (mayusculas y minusculas
  no importan, pero el resto debe coincidir).
- Cierra y vuelve a abrir el celular.
- En la computadora, abre Sincronizacion y dale al boton de sincronizar
  a mano.

## El programa no abre
Pasa a la pantalla de acceso y escribe el usuario y la contrasena que
creaste en el Paso 6.1.

---

# LO QUE NO DEBES HACER

- No ejecutes el Paso 1 antes que el Paso 2.
- No borres nada de Supabase a mano (yo ya borre los datos de prueba).
- No pierdas el archivo .bak: cuando borres datos, el programa guarda un
  respaldo en la misma carpeta.
