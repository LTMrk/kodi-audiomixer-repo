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
- Escribe automaticamente (con un pequeno retardo) la linea `Copy:` correspondiente,
  preferentemente **directamente en tu `config.txt` real** de Equalizer APO. Solo si eso
  falla (algunos sistemas restringen la escritura en `C:\Program Files\...` de forma poco
  clara) usa como alternativa un archivo propio del addon dentro de la carpeta de datos de
  Kodi, que en ese caso tu `config.txt` real debe incluir mediante una linea `Include:` (ver
  "Instalacion" mas abajo).
- Equalizer APO recarga el archivo en caliente: los cambios se oyen al instante, sin reiniciar Kodi ni el audio.
- **Varios dispositivos de salida**: si tienes Equalizer APO activo en mas de un dispositivo
  (p.ej. altavoces y auriculares), puedes elegir a cual de ellos se aplica la mezcla. El addon
  usa la directiva nativa de Equalizer APO `Device: <patron>` para que cada dispositivo tenga
  su propio bloque dentro del mismo `config.txt`, sin pisarse entre si.
- **Refleja el estado real del archivo al abrir**: en vez de arrancar siempre en los valores por
  defecto, lee el bloque ya guardado en `config.txt` para el dispositivo elegido (si existe) y
  coloca los sliders donde realmente estan aplicados ahora mismo.
- **Atajo de teclado (F9)**: se instala solo la primera vez que abres el addon. Pulsando F9 en
  cualquier pantalla, incluida la reproduccion de video a pantalla completa, se abre el
  mezclador directamente — no hace falta pasar por el menu contextual.

## Instalacion

### Opcion rapida (zip)
1. Ve a la seccion **Releases** de este repositorio y descarga el `.zip` de la ultima version.
2. En Kodi: **Ajustes > Complementos > Instalar desde archivo zip**, y selecciona el zip descargado.
3. Abre el addon desde **Complementos > Complementos de programa > Audio Channel Mixer**.

### Como escribe el addon (opcion A / opcion B)

1. **Opcion A (normal, sin pasos extra):** el addon intenta escribir directamente en tu
   `config.txt` real (Ajustes > Ruta de config.txt). Si tienes permisos de escritura ahi (la
   mayoria de instalaciones), no tienes que hacer nada mas — abre el addon y ya funciona.
2. **Opcion B (solo si la A falla):** si escribir en `config.txt` no es posible (algunos
   sistemas restringen `C:\Program Files\...` de forma poco clara, sin dar ni siquiera un
   error visible), el addon usa automaticamente un archivo propio dentro de la carpeta de
   datos de Kodi (`.../userdata/addon_data/script.audiomixer/kodi_audiomixer.txt`) y te lo
   indica en el titulo de la ventana (`[archivo de respaldo, revisa Include:]`). En ese caso
   hace falta **un paso manual, una sola vez**: te muestra un dialogo con la linea exacta a
   anadir al final de tu `config.txt` real, algo como:
   ```
   Include: "C:\Users\<tu-usuario>\AppData\Roaming\Kodi\userdata\addon_data\script.audiomixer\kodi_audiomixer.txt"
   ```
   Abre tu `config.txt` real con el Bloc de notas, pega esa linea al final y guarda. A partir
   de ahi, los cambios se aplican automaticamente (Equalizer APO recarga tanto `config.txt`
   como los archivos que incluye, en caliente).

### Ajustes del addon
Entra en **Complementos > Mis complementos > Audio Channel Mixer > Configurar**, y revisa:
- **Ruta de config.txt**: la ruta de tu `config.txt` real de Equalizer APO (por defecto
  `C:\Program Files\EqualizerAPO\config\config.txt`). Es donde el addon intenta escribir
  primero (opcion A); solo se usa para mostrar el aviso de `Include:` si hace falta caer a la
  opcion B.
- **Modo por defecto**: Simple o Avanzado.
- **Retardo de escritura**: milisegundos de espera tras soltar el slider antes de escribir el archivo (evita cortes si mueves varios sliders seguidos).
- **Dispositivo de salida > Detectar dispositivos y elegir...**: muestra los dispositivos de
  sonido detectados en el sistema (via WMI) y guarda el elegido como patron `Device:` de
  Equalizer APO. Elige **"Todos los dispositivos (global)"** si solo usas un dispositivo o
  quieres una mezcla unica para todos. El campo de texto **Dispositivo** debajo muestra el
  patron actual y tambien se puede editar a mano si el autodetectado no coincide exactamente
  con como Equalizer APO ve tu dispositivo (revisa el nombre real en tu `config.txt`, en la
  linea `Device:` que Equalizer APO anade automaticamente al arrancar).
- **Conservar configuracion existente en config.txt** (activado por defecto): con esto activado,
  el addon nunca toca nada de `config.txt` salvo su propio bloque marcado. Si lo desactivas, y
  la opcion A (escritura directa) esta funcionando, tambien se permite limpiar una linea
  `Include:` propia que hubiera quedado de una sesion anterior en modo B y ya no sirva de nada.
  Nunca toca ninguna otra configuracion (Peace GUI, etc.).
- **Instalar/reinstalar atajo de teclado (F9)**: repite la instalacion del atajo si lo has
  borrado, quieres forzar una recarga, o simplemente quieres confirmar que sigue ahi.

## Uso

- Pulsa **F9** en cualquier pantalla (incluida la reproduccion de video a pantalla completa)
  para abrir el mezclador directamente. También puedes abrirlo desde **Complementos >
  Complementos de programa > Audio Channel Mixer**, o desde el menu contextual del reproductor
  (tecla `C`, o clic derecho) si te funciona en tu configuracion.
- **Arriba/Abajo** mueve el foco entre los sliders (y llega a los botones en los extremos).
  **Izquierda/Derecha** sube o baja el porcentaje del slider con foco, en pasos del 2%.
- Con **raton**, haz clic en cualquier punto de la barra de un slider para poner el valor
  directamente en esa posicion; los botones tambien responden al clic.
- **Modo Simple**: 50% = mezcla estandar (sin cambios), 100% = doble de ganancia, 0% = silenciado.
- **Modo Avanzado**: el valor del slider es el coeficiente directo (0% a 200%) con el que ese canal de origen entra en esa salida.
- Boton **Cambiar a modo Avanzado/Simple** para alternar.
- Boton **Guardar y cerrar** (o Atras) para salir; el ultimo valor ya quedo escrito.

## Notas tecnicas

- Cada vez que abres el mezclador, el addon prueba a escribir en tu `config.txt` real
  (opcion A); solo si eso falla cae al archivo propio en `addon_data` (opcion B) para esa
  sesion. El titulo de la ventana indica `[archivo de respaldo, revisa Include:]` cuando esta
  en modo B.
- En cualquiera de los dos archivos, el addon nunca borra nada que no sea suyo: cada
  dispositivo (o el global, si no eliges ninguno) tiene su propio bloque marcado
  `# BEGIN KODI AUDIOMIXER [clave] ... # END KODI AUDIOMIXER [clave]`, y solo se reemplaza el
  bloque del dispositivo que estas editando.
- Si ni el `config.txt` real ni el archivo de respaldo se pueden escribir, revisa permisos y
  espacio en disco.

## Que pasa si algo no esta bien configurado

Antes de abrir la ventana del mezclador, el addon comprueba el entorno y avisa con un
dialogo explicando el problema (en vez de fallar en silencio o con un error tecnico) si:

- No estas en Windows (el addon solo funciona con Equalizer APO, que es Windows-only).
- No se puede escribir ni en tu `config.txt` real ni en el archivo de respaldo del addon:
  revisa permisos o espacio en disco.
- El archivo en el que va a escribir (real o de respaldo) tiene marcas `BEGIN/END KODI
  AUDIOMIXER` mal formadas (huerfanas, anidadas o duplicadas, por ejemplo por una edicion
  manual a medias): el addon **no abre la ventana ni toca el archivo**, te lista el problema
  exacto (con numero de linea) y te pide revisarlo a mano primero. Esto es a proposito: mejor
  avisar que arriesgarse a escribir sobre un archivo que no se puede interpretar con seguridad.
- Esta usando el archivo de respaldo (opcion B) y tu `config.txt` real todavia no tiene la
  linea `Include:` hacia el: te muestra el texto exacto a anadir. No bloquea el uso del addon,
  solo avisa — el audio no cambiara hasta que la anadas.
- Cualquier otro error inesperado al abrir la ventana queda registrado en el log de Kodi
  y se muestra un aviso, en lugar de un cierre silencioso del addon.
