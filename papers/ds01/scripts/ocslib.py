#!/usr/bin/env python3
"""D27 shared helpers: anonymous TAP/HTTP access for the DS-01 archival sweep.

No logins, no tokens, no cookies. Read-only public archives only.
"""
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

import certifi

CTX = ssl.create_default_context(cafile=certifi.where())
UA = "ocs-d27-archival/1.0 (anonymous public archive query)"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")
DATA = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

# DS-01
RA, DEC = 201.41849, -47.05715
GAIA_ID = 6083772968079356544

TAP = {
    "gaia": "https://gea.esac.esa.int/tap-server/tap/sync",
    "vizier": "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync",
    "heasarc": "https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync",
    "eso": "https://archive.eso.org/tap_obs/sync",
    "casda": "https://casda.csiro.au/casda_vo_tools/tap/sync",
    "datalab": "https://datalab.noirlab.edu/tap/sync",
    "irsa": "https://irsa.ipac.caltech.edu/TAP/sync",
    "simbad": "https://simbad.cds.unistra.fr/simbad/sim-tap/sync",
    "nrao": "https://data.nrao.edu/tap/sync",
    "cadc": "https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/tap/sync",
}


def _get(url, timeout=60, extra_headers=None):
    h = {"User-Agent": UA}
    if extra_headers:
        h.update(extra_headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.status, r.read()


def get_text(url, timeout=60, extra_headers=None):
    st, body = _get(url, timeout, extra_headers)
    return st, body.decode("utf-8", "replace")


def tap(name, adql, fmt="csv", timeout=180, save=None, maxrec=None):
    """Synchronous TAP query. name is a key of TAP or a full URL."""
    ep = TAP.get(name, name)
    form = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": fmt, "QUERY": adql}
    if maxrec is not None:
        form["MAXREC"] = str(maxrec)
    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(
        ep, data=data, headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            body = r.read()
            txt = body.decode("utf-8", "replace")
            status = r.status
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        status = e.code
    dt = time.time() - t0
    if save:
        with open(os.path.join(OUT, save), "w", encoding="utf-8") as f:
            f.write(txt)
    return status, txt, dt


def csv_rows(txt):
    """Parse a TAP CSV response into list of dicts, skipping VOTable/error bodies."""
    if txt.lstrip().startswith("<"):
        return None
    lines = [l for l in txt.splitlines() if l.strip() != ""]
    if not lines:
        return []
    hdr = [c.strip().strip('"') for c in lines[0].split(",")]
    rows = []
    for l in lines[1:]:
        if l.startswith("#"):
            continue
        parts = l.split(",")
        if len(parts) != len(hdr):
            continue
        rows.append({k: v.strip().strip('"') for k, v in zip(hdr, parts)})
    return rows


def vot_rows(txt):
    """Parse a VOTable (TABLEDATA) response into a list of dicts. Returns None on error."""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(txt)
    except Exception:
        return None
    info = root.iter("{http://www.ivoa.net/xml/VOTable/v1.3}INFO")
    for el in root.iter():
        if el.tag.endswith("INFO") and el.get("name") == "QUERY_STATUS" and el.get("value") == "ERROR":
            return None
    for res in root.iter():
        if not res.tag.endswith("RESOURCE"):
            continue
        fields = []
        for f in res.iter():
            if f.tag.endswith("FIELD"):
                fields.append(f.get("name"))
        for td in res.iter():
            if not td.tag.endswith("TABLEDATA"):
                continue
            out = []
            for tr in td:
                vals = []
                for cell in tr:
                    vals.append((cell.text or "").strip())
                if len(vals) == len(fields):
                    out.append(dict(zip(fields, vals)))
                elif fields and len(vals) != len(fields):
                    out.append({"_raw": vals})
            if out or fields:
                return out
    return []


def tap_vot(name, adql, timeout=240, save=None):
    """HEASARC-style TAP query returning VOTable, parsed to dicts."""
    ep = TAP.get(name, name)
    form = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "votable", "QUERY": adql}
    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(
        ep, data=data, headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            txt = r.read().decode("utf-8", "replace")
            status = r.status
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        status = e.code
    dt = time.time() - t0
    if save:
        with open(os.path.join(OUT, save), "w", encoding="utf-8") as f:
            f.write(txt)
    return status, txt, dt, heasarc_rows(txt)


def vot_binary_rows(txt):
    """Decode a VOTable whose DATA is BINARY/base64 (HEASARC style) into dicts."""
    import base64
    import struct
    import xml.etree.ElementTree as ET

    NS = "{http://www.ivoa.net/xml/VOTable/v1.3}"
    try:
        root = ET.fromstring(txt)
    except Exception:
        return None
    for el in root.iter():
        if el.tag.endswith("INFO") and el.get("name") == "QUERY_STATUS" and el.get("value") == "ERROR":
            return None

    SIZE = {"short": 2, "int": 4, "long": 8, "float": 4, "double": 8, "boolean": 1,
            "unsignedByte": 1, "char": 1, "unicodeChar": 2}
    FMT = {"short": ">h", "int": ">i", "long": ">q", "float": ">f", "double": ">d",
           "boolean": ">B", "unsignedByte": ">B"}

    for table in root.iter(NS + "TABLE"):
        fields = []
        for f in table.findall(NS + "FIELD"):
            fields.append((f.get("name"), f.get("datatype"), f.get("arraysize")))
        stream = None
        for st_el in table.iter(NS + "STREAM"):
            stream = st_el
        if stream is None or not (stream.text or "").strip():
            return []
        raw = base64.b64decode("".join(stream.text.split()))
        pos = 0
        out = []
        n = len(fields)
        while pos < len(raw):
            row = {}
            ok = True
            for name, dt, arr in fields:
                if dt in ("char", "unicodeChar"):
                    if arr == "*" or arr is None:
                        if pos + 4 > len(raw):
                            ok = False
                            break
                        ln = struct.unpack_from(">i", raw, pos)[0]
                        pos += 4
                        if ln < 0 or pos + ln > len(raw):
                            ok = False
                            break
                        row[name] = raw[pos:pos + ln].decode("utf-8", "replace").strip()
                        pos += ln
                    else:
                        ln = int(arr)
                        row[name] = raw[pos:pos + ln].decode("utf-8", "replace").strip()
                        pos += ln
                else:
                    if dt not in FMT:
                        ok = False
                        break
                    k = 1
                    if arr and arr not in ("*",):
                        k = int(arr.split("x")[0]) if "x" in arr else int(arr)
                    sz = SIZE[dt] * k
                    if pos + sz > len(raw):
                        ok = False
                        break
                    if k == 1:
                        row[name] = struct.unpack_from(FMT[dt], raw, pos)[0]
                    else:
                        row[name] = [struct.unpack_from(FMT[dt], raw, pos + i * SIZE[dt])[0]
                                     for i in range(k)]
                    pos += sz
            if not ok:
                break
            out.append(row)
        return out
    return []


def heasarc_rows(txt):
    """Return rows from a HEASARC VOTable, TABLEDATA or BINARY."""
    r = vot_rows(txt)
    if r:
        return r
    return vot_binary_rows(txt)


def report(tag, status, txt, dt=None):
    head = txt[:300].replace("\n", " | ") if txt else ""
    print(f"[{tag}] status={status} dt={dt:.1f}s" if dt is not None else f"[{tag}] status={status}")
    print("   " + head)


if __name__ == "__main__":
    print("helpers ok; OUT=", OUT)
