# -*- coding: utf-8 -*-
import os
import io
import re

GLOBAL_KEY = "GLOBAL"

# El grupo entre corchetes es opcional para reconocer tambien las marcas
# "planas" (sin dispositivo) que escribian las versiones 1.0.0-1.0.4; esas
# se tratan como la clave GLOBAL_KEY.
BEGIN_RE = re.compile(r'^# BEGIN KODI AUDIOMIXER(?: \[(.*)\])? .*$')
END_RE = re.compile(r'^# END KODI AUDIOMIXER(?: \[(.*)\])?\s*$')


class ApoWriteError(Exception):
    pass


class ApoFormatError(ApoWriteError):
    """El archivo tiene marcas BEGIN/END mal formadas (huerfanas, anidadas,
    duplicadas...). Se distingue de ApoWriteError para poder avisar de forma
    especifica sin arriesgarse a tocar un archivo que no se entiende bien."""
    pass


def _begin_mark(key):
    return "# BEGIN KODI AUDIOMIXER [%s] (no editar a mano esta seccion)" % key


def _end_mark(key):
    return "# END KODI AUDIOMIXER [%s]" % key


def _read_lines(path):
    if not os.path.exists(path):
        return []
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except (IOError, OSError) as e:
        raise ApoWriteError(str(e))


def scan_blocks(lines):
    """Recorre las lineas buscando pares BEGIN/END de KODI AUDIOMIXER.

    Devuelve (blocks, problems):
      blocks: dict clave -> (indice_inicio, indice_fin) de cada par valido.
      problems: lista de strings describiendo cualquier BEGIN/END huerfano,
                anidado o duplicado, con su numero de linea (1-based).
    """
    blocks = {}
    problems = []
    open_key = None
    open_line = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        m = BEGIN_RE.match(stripped)
        if m:
            key = m.group(1) if m.group(1) is not None else GLOBAL_KEY
            if open_key is not None:
                problems.append(
                    "BEGIN de '%s' en linea %d sin un END de '%s' antes "
                    "(abierto en linea %d)" % (key, i + 1, open_key, open_line + 1))
            open_key, open_line = key, i
            continue
        m = END_RE.match(stripped)
        if m:
            key = m.group(1) if m.group(1) is not None else GLOBAL_KEY
            if open_key is None:
                problems.append("END de '%s' en linea %d sin un BEGIN antes" % (key, i + 1))
                continue
            if key != open_key:
                problems.append(
                    "END de '%s' en linea %d no coincide con el BEGIN de '%s' "
                    "en linea %d" % (key, i + 1, open_key, open_line + 1))
                open_key, open_line = None, None
                continue
            if key in blocks:
                problems.append(
                    "Bloque duplicado para '%s' (lineas %d-%d y %d-%d)" % (
                        key, blocks[key][0] + 1, blocks[key][1] + 1, open_line + 1, i + 1))
            else:
                blocks[key] = (open_line, i)
            open_key, open_line = None, None
    if open_key is not None:
        problems.append(
            "BEGIN de '%s' en linea %d sin END hasta el final del archivo" % (
                open_key, open_line + 1))
    return blocks, problems


def validate(path):
    """Devuelve la lista de problemas de formato encontrados (vacia si todo bien)."""
    lines = _read_lines(path)
    _, problems = scan_blocks(lines)
    return problems


def read_block(path, key):
    """Devuelve la lista de lineas (sin las marcas) del bloque de esa clave,
    o None si ese bloque no existe todavia. Lanza ApoFormatError si el
    archivo tiene marcas BEGIN/END mal formadas en cualquier bloque."""
    lines = _read_lines(path)
    blocks, problems = scan_blocks(lines)
    if problems:
        raise ApoFormatError("; ".join(problems))
    if key not in blocks:
        return None
    start, end = blocks[key]
    return lines[start + 1:end]


def write_block(path, key, body_lines):
    """Inserta o reemplaza el bloque marcado de 'key', dejando intacto el
    resto del config.txt (incluidos los bloques de otras claves/dispositivos).

    Si el archivo tiene marcas BEGIN/END mal formadas en cualquier bloque no
    se toca nada y se lanza ApoFormatError, para no arriesgarse a corromper
    un archivo que no se puede interpretar con seguridad.
    """
    lines = _read_lines(path)
    blocks, problems = scan_blocks(lines)
    if problems:
        raise ApoFormatError("; ".join(problems))

    block = [_begin_mark(key)] + list(body_lines) + [_end_mark(key)]

    if key in blocks:
        start, end = blocks[key]
        new_lines = lines[:start] + block + lines[end + 1:]
    else:
        if lines and lines[-1].strip() != "":
            lines.append("")
        new_lines = lines + block

    try:
        with io.open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
    except (IOError, OSError) as e:
        raise ApoWriteError(str(e))


def rewrite_keep_only_own_blocks(path):
    """Reescribe el archivo dejando SOLO los bloques propios ya existentes
    (# BEGIN/END KODI AUDIOMIXER [...]), descartando cualquier otra linea
    (Include:/Device:/Channel: de otras herramientas, comentarios, etc.).
    Se usa solo cuando el usuario desactiva explicitamente "conservar
    configuracion existente". Lanza ApoFormatError si el archivo tiene
    marcas mal formadas (no se toca nada en ese caso). Devuelve True si el
    contenido ha cambiado, False si ya estaba asi."""
    lines = _read_lines(path)
    blocks, problems = scan_blocks(lines)
    if problems:
        raise ApoFormatError("; ".join(problems))

    new_lines = []
    for start, end in sorted(blocks.values()):
        if new_lines:
            new_lines.append("")
        new_lines.extend(lines[start:end + 1])

    if new_lines == lines:
        return False

    try:
        with io.open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n" if new_lines else "")
    except (IOError, OSError) as e:
        raise ApoWriteError(str(e))
    return True
