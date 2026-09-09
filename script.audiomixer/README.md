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
- Escribe automaticamente (con un pequeno retardo) la linea `Copy:` correspondiente en un
  archivo propio del addon (dentro de la carpeta de datos de Kodi, nunca en
  `C:\Program Files\...`), que tu `config.txt` real de Equalizer APO incluye mediante una
  linea `Include:` (ver "Instalacion" mas abajo) — asi el addon nunca depende de tener
  permisos de escritura sobre la carpeta de Equalizer APO.
- Equalizer APO recarga el archivo en caliente: los cambios se oyen al instante, sin reiniciar Kodi ni el audio.
- **Varios dispositivos de salida**: si tienes Equalizer APO activo en mas de un dispositivo
  (p.ej. altavoces y auriculares), puedes elegir a cual de ellos se aplica la mezcla. El addon
  usa la directiva nativa de Equalizer APO `Device: <patron>` para que cada dispositivo tenga
  su propio bloque dentro del mismo `config.txt`, sin pisarse entre si.
- **Refleja el estado real del archivo al abrir**: en vez de arrancar siempre en los valores por
  defecto, lee el bloque ya guardado en `config.txt` para el dispositivo elegido (si existe) y
  coloca los sliders donde realmente estan aplicados ahora mismo.

## Instalacion

### Opcion rapida (zip)
1. Ve a la seccion **Releases** de este repositorio y descarga el `.zip` de la ultima version.
2. En Kodi: **Ajustes > Complementos > Instalar desde archivo zip**, y selecciona el zip descargado.
3. Abre el addon desde **Complementos > Complementos de programa > Audio Channel Mixer**.

### Paso unico: enlazar con tu config.txt real

El addon **nunca escribe directamente** en `C:\Program Files\EqualizerAPO\config\config.txt`
(esa carpeta suele estar protegida y dar problemas de permisos poco fiables). En su lugar,
escribe en un archivo propio dentro de la carpeta de datos de Kodi
(`.../userdata/addon_data/script.audiomixer/kodi_audiomixer.txt`), y tu `config.txt` real solo
necesita **una linea, anadida una sola vez**, para incluirlo:

1. Abre el addon una vez (Complementos > Complementos de programa > Audio Channel Mixer). Si
   tu `config.txt` real (ver Ajustes) todavia no tiene esa linea, te mostrara un dialogo con el
   texto exacto a copiar, algo como:
   ```
   Include: "C:\Users\<tu-usuario>\AppData\Roaming\Kodi\userdata\addon_data\script.audiomixer\kodi_audiomixer.txt"
   ```
2. Abre tu `config.txt` real con el Bloc de notas y pega esa linea al final, luego guarda.
3. Listo — a partir de ahi, cualquier cambio que hagas con los sliders se aplica automaticamente
   (Equalizer APO recarga tanto `config.txt` como los archivos que incluye en caliente).

### Ajustes del addon
Entra en **Complementos > Mis complementos > Audio Channel Mixer > Configurar**, y revisa:
- **Ruta de config.txt**: la ruta de tu `config.txt` REAL de Equalizer APO (por defecto
  `C:\Program Files\EqualizerAPO\config\config.txt`). El addon la usa solo para comprobar si ya
  tiene la linea `Include:` de arriba y para poder avisarte si falta — no escribe ahi.
- **Modo por defecto**: Simple o Avanzado.
- **Retardo de escritura**: milisegundos de espera tras soltar el slider antes de escribir el archivo (evita cortes si mueves varios sliders seguidos).
- **Dispositivo de salida > Detectar dispositivos y elegir...**: muestra los dispositivos de
  sonido detectados en el sistema (via WMI) y guarda el elegido como patron `Device:` de
  Equalizer APO. Elige **"Todos los dispositivos (global)"** si solo usas un dispositivo o
  quieres una mezcla unica para todos. El campo de texto **Dispositivo** debajo muestra el
  patron actual y tambien se puede editar a mano si el autodetectado no coincide exactamente
  con como Equalizer APO ve tu dispositivo (revisa el nombre real en tu `config.txt`, en la
  linea `Device:` que Equalizer APO anade automaticamente al arrancar).

## Uso

- **Mientras reproduces video**, abre el menu contextual (boton de contexto del mando/skin,
  tecla `C` en teclado, o el icono "..." del OSD en skins como Estuary) y elige
  **"Mezclador de canales (Audio Channel Mixer)"**. Tambien puedes abrirlo en cualquier
  momento desde **Complementos > Complementos de programa > Audio Channel Mixer**.
- Mueve los sliders con las flechas del mando/teclado.
- **Modo Simple**: 50% = mezcla estandar (sin cambios), 100% = doble de ganancia, 0% = silenciado.
- **Modo Avanzado**: el valor del slider es el coeficiente directo (0% a 200%) con el que ese canal de origen entra en esa salida.
- Boton **Cambiar a modo Avanzado/Simple** para alternar.
- Boton **Guardar y cerrar** (o Atras) para salir; el ultimo valor ya quedo escrito.

## Notas tecnicas

- El addon escribe siempre en `.../userdata/addon_data/script.audiomixer/kodi_audiomixer.txt`,
  nunca en tu `config.txt` real — este ultimo solo necesita la linea `Include:` de arriba,
  anadida una vez a mano. Esto evita depender de permisos de escritura sobre
  `C:\Program Files\...`, que en algunos sistemas fallan de forma poco clara (sin excepcion ni
  error visible, sin llegar a escribir realmente).
- Dentro de ese archivo propio, el addon nunca borra nada que no sea suyo: cada dispositivo (o
  el global, si no eliges ninguno) tiene su propio bloque marcado `# BEGIN KODI AUDIOMIXER
  [clave] ... # END KODI AUDIOMIXER [clave]`, y solo se reemplaza el bloque del dispositivo que
  estas editando.
- Si escribir ese archivo propio falla, revisa el espacio en disco o los permisos de tu perfil
  de Kodi (`userdata`) — no deberia depender nunca de `Program Files`.

## Que pasa si algo no esta bien configurado

Antes de abrir la ventana del mezclador, el addon comprueba el entorno y avisa con un
dialogo explicando el problema (en vez de fallar en silencio o con un error tecnico) si:

- No estas en Windows (el addon solo funciona con Equalizer APO, que es Windows-only).
- No se puede escribir en el archivo propio del addon (dentro de `userdata`): revisa espacio
  en disco o permisos de tu perfil de Kodi — no deberia pasar en un uso normal.
- Ese archivo propio tiene marcas `BEGIN/END KODI AUDIOMIXER` mal formadas (huerfanas, anidadas
  o duplicadas, por ejemplo por una edicion manual a medias): el addon **no abre la ventana ni
  toca el archivo**, te lista el problema exacto (con numero de linea) y te pide revisarlo a
  mano primero. Esto es a proposito: mejor avisar que arriesgarse a escribir sobre un archivo
  que no se puede interpretar con seguridad.
- Tu `config.txt` real todavia no tiene la linea `Include:` hacia el archivo del addon: te
  muestra el texto exacto a anadir (ver "Paso unico" mas arriba). No bloquea el uso del addon,
  solo avisa — el audio no cambiara hasta que la anadas.
- Cualquier otro error inesperado al abrir la ventana queda registrado en el log de Kodi
  y se muestra un aviso, en lugar de un cierre silencioso del addon.
