# -*- coding: utf-8 -*-
import os
import io

BEGIN_MARK = "# BEGIN KODI AUDIOMIXER (no editar a mano esta seccion)"
END_MARK = "# END KODI AUDIOMIXER"


class ApoWriteError(Exception):
    pass


def _read_lines(path):
    if not os.path.exists(path):
        return []
    with io.open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def _find_block(lines):
    start = end = -1
    for i, line in enumerate(lines):
        if line.strip() == BEGIN_MARK:
            start = i
        elif line.strip() == END_MARK:
            end = i
            break
    if start != -1 and end != -1 and end > start:
        return start, end
    return None, None


def write_copy_line(path, copy_line):
    """
    Inserta o reemplaza el bloque marcado que contiene la linea Copy:
    generada por el addon, dejando el resto del config.txt intacto.
    """
    lines = _read_lines(path)
    start, end = _find_block(lines)

    block = [BEGIN_MARK, copy_line, END_MARK]

    if start is not None:
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


def read_existing_copy_line(path):
    """Devuelve la linea Copy: guardada previamente por el addon, o None."""
    lines = _read_lines(path)
    start, end = _find_block(lines)
    if start is None:
        return None
    for line in lines[start:end]:
        if line.strip().startswith("Copy:"):
            return line.strip()
    return None
