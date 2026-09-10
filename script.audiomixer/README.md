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
- Modo **Avanzado** (12 controles): la contribucion de cada uno de los 6 canales de origen a la salida L, y por separado a la salida R. Panel ampliado y pistas mas grandes que antes, para que sean faciles de acertar con mando (D-pad o air-mouse).
- **Cambiar entre Simple y Avanzado en la misma sesion conserva los valores** (convertidos al
  equivalente del otro modo, con la misma formula que se usa para leer/escribir `config.txt`):
  Simple -> Avanzado -> Simple es exacto; Avanzado -> Simple es una aproximacion razonable
  (un unico fader por grupo en Simple no puede representar una mezcla asimetrica hecha en
  Avanzado), con una desviacion de como mucho 1 punto porcentual por redondeo.
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
- **Atajo de teclado configurable** (F9 por defecto, elegible entre F2-F12 en Ajustes): se
  instala solo la primera vez que abres el addon, o al cambiar de tecla. Pulsandolo en
  cualquier pantalla, incluida la reproduccion de video a pantalla completa, se abre el
  mezclador directamente — no hace falta pasar por el menu contextual.
- **Vumetro L/R en tiempo real**: dos barras (debajo del boton de modo) que muestran el nivel
  de la salida de audio real, tal y como suena, capturada por loopback WASAPI del dispositivo
  de reproduccion **por defecto** de Windows. Verde/amarillo/rojo segun el nivel. Si no se
  puede capturar audio por lo que sea (formato no soportado, dispositivo ocupado, etc.) el
  vumetro simplemente no aparece; el resto del mezclador sigue funcionando igual.
  **Limitacion:** mide el dispositivo por defecto del sistema, no necesariamente el
  dispositivo concreto que tengas elegido en Ajustes > Dispositivo de salida si usas varios.

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
  el addon nunca toca nada de `config.txt` salvo su propio bloque marcado.
  **Si lo desactivas** (y la opcion A -- escritura directa -- esta funcionando), cada vez que
  abras el addon **reescribe config.txt entero**, dejando solo los bloques propios del addon
  (de todos los dispositivos que tengas configurados) y descartando cualquier otra cosa que
  hubiera ahi -- incluido `Include: peace.txt` si usas Peace GUI. Usalo solo si quieres que
  `config.txt` sea de uso exclusivo de este addon.
- **Tecla rapida actual / Elegir tecla rapida...**: muestra la tecla activa (F9 por defecto) y
  deja elegir otra de F2 a F12, **"Detectar pulsando el boton..."** (recomendado: abre una
  pantalla que captura automaticamente el codigo real del siguiente boton que pulses -- sin
  tener que leer ni convertir nada a mano; solo funciona en **Kodi 21 "Omega" o posterior**,
  por un bug de versiones anteriores que impedia a los addons en Python leer ese codigo, ver
  [xbmc/xbmc#23789](https://github.com/xbmc/xbmc/pull/23789)), o **"Otra (codigo
  hexadecimal)..."** para introducirlo a mano si tu Kodi es mas antiguo. Para averiguar su
  codigo a mano: activa
  **Ajustes > Sistema > Registros > Activar registro de depuracion**, pulsa el boton una vez
  y busca en el Log Viewer la linea `CInputManager::HandleKey: ... (0xXXXX, obc-NNNNN) pressed`
  -- el codigo a introducir es el **hexadecimal entre parentesis** (`0xXXXX`, con o sin el
  `0x`). **El numero `obc-NNNNN` no sirve**: es un valor solo informativo que Kodi calcula mal
  para botones con un scancode grande (bug conocido, ver
  [xbmc/xbmc#16834](https://github.com/xbmc/xbmc/issues/16834)); usarlo directamente no llega
  a emparejar la tecla. Al cambiar de tecla se reinstala el atajo automaticamente.
  Ojo: si tu mando es un "air mouse" tipo **MX3** (muy comun), los 4 botones de colores son
  **solo IR** (no mandan nada por el dongle 2.4G) y no sirven para esto; usa otro boton que sí
  se vea reflejado en el log al pulsarlo. El campo "Tecla rapida actual" es **de solo lectura**
  (solo lo cambia "Elegir tecla rapida...") -- si escribieras ahi un texto como `f200` a mano,
  Kodi lo interpretaria como el NOMBRE literal de una tecla (que no existe), no como el
  hexadecimal `0xf200`, y el atajo se quedaria roto sin avisar; por eso ya no se puede editar
  directamente.

- Pulsa tu **tecla rapida** (F9 por defecto, configurable en Ajustes) en cualquier pantalla
  (incluida la reproduccion de video a pantalla completa) para abrir el mezclador directamente.
  También puedes abrirlo desde **Complementos > Complementos de programa > Audio Channel
  Mixer**, o desde el menu contextual del reproductor (tecla `C`, o clic derecho) si te
  funciona en tu configuracion.
- **Arriba/Abajo** mueve el foco entre los sliders (y llega a los botones en los extremos), que
  se resaltan con un brillo translucido para saber en todo momento sobre cual estas sin usar el
  raton. **Izquierda/Derecha** sube o baja el porcentaje del slider con foco, en pasos del 2%.
  **OK/Intro** sobre "Cambiar de modo" o "Guardar y cerrar" los activa igual que un clic.
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
- Con **"Conservar configuracion existente"** activado (por defecto), el addon nunca borra
  nada que no sea suyo, en ninguno de los dos archivos: cada dispositivo (o el global, si no
  eliges ninguno) tiene su propio bloque marcado
  `# BEGIN KODI AUDIOMIXER [clave] ... # END KODI AUDIOMIXER [clave]`, y solo se reemplaza el
  bloque del dispositivo que estas editando. **Desactivado**, cada apertura del addon reescribe
  `config.txt` dejando solo esos bloques propios (ver "Ajustes del addon" mas arriba).
- Si ni el `config.txt` real ni el archivo de respaldo se pueden escribir, revisa permisos y
  espacio en disco.
- El clic de raton sobre "Cambiar de modo"/"Guardar y cerrar" ya se gestionaba a mano por
  coordenadas (ver mas arriba) porque el clic nativo de Kodi (`OnClick`/`onControl`) no llega
  de forma fiable en algunos entornos. Se confirmo (con el addon separado **Identificador de
  Teclas/Mando**, `script.keyidentifier`, incluido en este mismo repositorio) que **OK/Intro
  por teclado o mando tampoco llegaba** por el mismo motivo -- ahora tambien se gestiona a
  mano (segun que control tenga el foco al recibir la accion `ACTION_SELECT_ITEM`), igual que
  el clic de raton.

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
