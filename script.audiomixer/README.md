# Audio Channel Mixer (EQ APO) — addon de Kodi

Controla en tiempo real la ganancia de cada canal de origen de un audio 5.1
(L, R, C, LFE, SL, SR) dentro de la mezcla final a estereo que hace
**Equalizer APO** en Windows. Pensado para poder subir el dialogo (canal
Central) sin tocar el resto, aunque tu salida final sean solo 2 altavoces.

Requisitos previos (fuera del addon):
- Windows con **Equalizer APO** instalado en el dispositivo de salida, configurado a 6 canales (5.1).
- **Peace GUI** es opcional (sirve para EQ por canal), este addon no lo sustituye: solo controla la matriz de mezcla (el `Copy:` del `config.txt`).

## Que hace

- Modo **Simple** (4 controles): Frontales L/R, Central, LFE, Surround (SL/SR juntos).
- Modo **Avanzado** (12 controles): la contribucion de cada uno de los 6 canales de origen a la salida L, y por separado a la salida R.
- Escribe automaticamente (con un pequeno retardo) la linea `Copy:` correspondiente en un bloque marcado de tu `config.txt`, sin tocar el resto de tu configuracion de Equalizer APO.
- Equalizer APO recarga el archivo en caliente: los cambios se oyen al instante, sin reiniciar Kodi ni el audio.

## Instalacion

### Opcion rapida (zip)
1. Ve a la seccion **Releases** de este repositorio y descarga el `.zip` de la ultima version.
2. En Kodi: **Ajustes > Complementos > Instalar desde archivo zip**, y selecciona el zip descargado.
3. Abre el addon desde **Complementos > Complementos de programa > Audio Channel Mixer**.

### Ajustes del addon
Antes de usarlo, entra en **Complementos > Mis complementos > Audio Channel Mixer > Configurar**, y revisa:
- **Ruta de config.txt**: por defecto `C:\Program Files\EqualizerAPO\config\config.txt`. Cambiala si tu instalacion esta en otra ruta.
- **Modo por defecto**: Simple o Avanzado.
- **Retardo de escritura**: milisegundos de espera tras soltar el slider antes de escribir el archivo (evita cortes si mueves varios sliders seguidos).

## Uso

- **Mientras reproduces video**, abre el menu contextual (boton de contexto del mando/skin,
  tecla `C` en teclado, o el icono "..." del OSD en skins como Estuary) y elige
  **"Mezclador de canales (Audio Channel Mixer)"**. Tambien puedes abrirlo en cualquier
  momento desde **Complementos > Complementos de programa > Audio Channel Mixer**.
- Mueve los sliders con las flechas del mando/teclado.
- **Modo Simple**: 50% = mezcla estandar (sin cambios), 100% = doble de ganancia, 0% = silenciado.
- **Modo Avanzado**: el valor del slider es el coeficiente directo (0% a 200%) con el que ese canal de origen entra en esa salida.
- Boton **Cambiar a modo Avanzado/Simple** para alternar.
- Boton **Guardar y cerrar** (o Atras) para salir; el ultimo valor ya quedo escrito en `config.txt`.

## Notas tecnicas

- El addon nunca borra el resto de tu `config.txt`: solo gestiona el contenido entre las marcas `# BEGIN KODI AUDIOMIXER` y `# END KODI AUDIOMIXER`.
- Si escribir el archivo falla (por ejemplo por permisos de `Program Files`), da permisos de escritura a tu usuario sobre la carpeta `EqualizerAPO\config`.

## Que pasa si algo no esta bien configurado

Antes de abrir la ventana del mezclador, el addon comprueba el entorno y avisa con un
dialogo explicando el problema (en vez de fallar en silencio o con un error tecnico) si:

- No estas en Windows (el addon solo funciona con Equalizer APO, que es Windows-only).
- No hay una ruta de `config.txt` configurada en los Ajustes del addon.
- La carpeta configurada no existe (probable indicio de que Equalizer APO no esta instalado,
  o la ruta esta mal).
- `config.txt` no existe en esa ruta: te pregunta si quieres continuar de todas formas
  (creara el archivo) o cancelar para revisar la ruta.
- No hay permisos de escritura sobre esa carpeta: te lo dice explicitamente en vez de morir
  con una excepcion.
- Cualquier otro error inesperado al abrir la ventana queda registrado en el log de Kodi
  y se muestra un aviso, en lugar de un cierre silencioso del addon.
