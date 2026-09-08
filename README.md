# kodi-audiomixer-repo

Repositorio Kodi para el addon **Audio Channel Mixer (EQ APO)** (`script.audiomixer`):
controla en tiempo real la ganancia de cada canal de origen de un audio 5.1 (L, R, C,
LFE, SL, SR) dentro de la mezcla final a estereo que hace **Equalizer APO** en Windows.

Ver [`script.audiomixer/README.md`](script.audiomixer/README.md) para el detalle del
addon (requisitos, ajustes, uso).

## Instalacion en Kodi (recomendado: via repositorio, con autoactualizacion)

1. En Kodi, ve a **Ajustes > Sistema > Complementos** y activa **Fuentes desconocidas**.
2. Ve a **Ajustes > Complementos > Instalar desde archivo zip**.
3. Anade como fuente de archivos la URL de este repositorio:
   `https://raw.githubusercontent.com/LTMrk/kodi-audiomixer-repo/main/`
   (Complementos > Instalar desde archivo zip > raiz del sistema de archivos >
   Anadir fuente de red, pega la URL de arriba y ponle un nombre, por ejemplo `AudioMixerRepo`).
4. Entra en esa fuente y selecciona `repository.audiomixerrepo/repository.audiomixerrepo-1.0.0.zip`
   para instalar el **repositorio**.
5. Una vez instalado el repositorio, ve a **Complementos > Instalar desde repositorio >
   Audio Mixer Repository > Complementos de programa > Audio Channel Mixer (EQ APO)** e
   instalalo desde ahi. A partir de este momento Kodi detectara y ofrecera las
   actualizaciones del addon automaticamente cada vez que se publique una nueva version
   en este repositorio.

## Instalacion rapida (solo el addon, sin autoactualizacion)

1. Descarga `script.audiomixer/script.audiomixer-1.0.0.zip` de este repositorio (boton
   "Raw" o desde la seccion Releases si existe).
2. En Kodi: **Ajustes > Complementos > Instalar desde archivo zip**, y selecciona el zip
   descargado.

## Estructura del repositorio

```
addons.xml                                    # indice de addons (autogenerado)
addons.xml.md5                                # checksum de addons.xml
script.audiomixer/                            # el addon
  addon.xml
  script.audiomixer-1.0.0.zip                 # paquete instalable del addon
repository.audiomixerrepo/                    # el "meta-addon" repositorio Kodi
  addon.xml
  repository.audiomixerrepo-1.0.0.zip         # paquete instalable del repositorio
```

## Publicar una nueva version del addon

Al subir una nueva version de `script.audiomixer`:

1. Sube el numero de `version` en `script.audiomixer/addon.xml`.
2. Genera el zip `script.audiomixer/script.audiomixer-<version>.zip` (debe contener la
   carpeta `script.audiomixer/` con todos sus archivos dentro, no el contenido suelto).
3. Regenera `addons.xml` concatenando los `addon.xml` de `script.audiomixer` y
   `repository.audiomixerrepo` dentro de una unica etiqueta `<addons>...</addons>`.
4. Regenera `addons.xml.md5` con el md5 (hex) del nuevo `addons.xml`.
5. Haz commit y push a `main`. Kodi comprobara `addons.xml.md5` periodicamente y
   ofrecera la actualizacion a quien tenga el repositorio instalado.

## Licencia

MIT. Ver [`script.audiomixer/LICENSE`](script.audiomixer/LICENSE).
