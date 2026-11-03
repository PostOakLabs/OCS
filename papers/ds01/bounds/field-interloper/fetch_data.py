"""Fetch the inputs for OCS-DS01-BOUNDS-FIELD-INTERLOPER-1.

Everything goes under the shared cache with a MANIFEST row. Idempotent: an
existing file with the recorded sha256 is reused, not re-fetched.

Archives: Gaia DR3 TAP and VizieR TAP (VI/137). Nothing else.
"""

import csv
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

CACHE = r"C:\farm\cache\omegacen\ds01-bounds-field-interloper"
RAW = os.path.join(CACHE, "raw")
MANIFEST = os.path.join(CACHE, "MANIFEST.csv")

GAIA = "https://gea.esac.esa.int/tap-server/tap/sync"
VIZIER = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"

L_C, B_C = 309.101888687704, 14.968236020672741
CONES = [(-6, 193.104407, -47.903188), (-4, 195.984182, -47.850843),
         (-3, 197.420239, -47.791195), (3, 205.899272, -46.972709),
         (4, 207.278117, -46.761474), (6, 209.996618, -46.277392)]

GAIA_COLS = ("source_id,ra,dec,parallax,parallax_error,parallax_over_error,"
             "pmra,pmdec,pmra_error,pmdec_error,pmra_pmdec_corr,"
             "phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag,bp_rp,"
             "ruwe,astrometric_excess_noise,astrometric_excess_noise_sig,"
             "phot_variable_flag,ipd_gof_harmonic_amplitude,"
             "ipd_frac_multi_peak,visibility_periods_used,"
             "astrometric_params_solved,ref_epoch")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tap(url, query, fmt="csv", timeout=900):
    body = urllib.parse.urlencode({"REQUEST": "doQuery", "LANG": "ADQL",
                                   "FORMAT": fmt, "QUERY": query}).encode()
    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        return fh.read()


def manifest_has(relpath):
    if not os.path.exists(MANIFEST):
        return None
    with open(MANIFEST, newline="") as fh:
        for row in csv.DictReader(fh):
            if row["relpath"] == relpath:
                return row
    return None


def manifest_add(relpath, path, source, note):
    new = not os.path.exists(MANIFEST)
    with open(MANIFEST, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["relpath", "bytes", "sha256", "source", "fetched_utc",
                        "note"])
        w.writerow([relpath, os.path.getsize(path), sha256(path), source,
                    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    note])


def fetch(relpath, source, fn, note):
    path = os.path.join(RAW, relpath)
    rec = manifest_has(relpath)
    if rec and os.path.exists(path) and sha256(path) == rec["sha256"]:
        print(f"cached  {relpath}  {os.path.getsize(path)} bytes")
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = fn()
    with open(path, "wb") as fh:
        fh.write(data)
    if rec:
        manifest_add(relpath, path, source, note + " (refetched)")
    else:
        manifest_add(relpath, path, source, note)
    print(f"fetched {relpath}  {len(data)} bytes")
    return path


def main():
    os.makedirs(RAW, exist_ok=True)

    # 1. Gaia DR3 control cones, identical column list to the D189 cone.
    for dl, ra, dec in CONES:
        name = f"control_dl{dl:+d}.csv"
        q = (f"SELECT {GAIA_COLS} FROM gaiadr3.gaia_source "
             f"WHERE CONTAINS(POINT('ICRS',ra,dec),"
             f"CIRCLE('ICRS',{ra},{dec},0.5))=1")
        fetch(name, "Gaia DR3 TAP gaiadr3.gaia_source", lambda q=q: tap(GAIA, q),
              f"30 arcmin cone at l_c{dl:+d}, b_c")

    # 2. Independent counts for reconciliation.
    rows = []
    for dl, ra, dec in CONES:
        q = (f"SELECT COUNT(*) AS n FROM gaiadr3.gaia_source "
             f"WHERE CONTAINS(POINT('ICRS',ra,dec),"
             f"CIRCLE('ICRS',{ra},{dec},0.5))=1")
        d = json.loads(tap(GAIA, q, fmt="json"))
        rows.append({"dl": dl, "count_star": d["data"][0][0]})
        time.sleep(1.0)
    q = ("SELECT COUNT(*) AS n FROM gaiadr3.gaia_source "
         "WHERE CONTAINS(POINT('ICRS',ra,dec),"
         "CIRCLE('ICRS',201.696833,-47.479583,0.5833))=1")
    ann = json.loads(tap(GAIA, q, fmt="json"))["data"][0][0]
    out = {"cones": rows, "annulus_35arcmin": ann}
    path = os.path.join(RAW, "gaia_counts.json")
    with open(path, "w", newline="\n") as fh:
        json.dump(out, fh, indent=1)
    manifest_add("gaia_counts.json", path, "Gaia DR3 TAP COUNT(*)",
                 "reconciliation counts for the six cones and the 35 arcmin cone")

    # 3. Every Gaia DR3 CV-class source, joined to the source table.
    q = ("SELECT v.source_id, v.best_class_name, v.best_class_score, "
         "g.ra, g.dec, g.phot_g_mean_mag, g.bp_rp, g.parallax, "
         "g.parallax_error, g.parallax_over_error, g.pmra, g.pmdec, "
         "g.pmra_error, g.pmdec_error, g.ruwe, g.astrometric_params_solved "
         "FROM gaiadr3.vari_classifier_result AS v "
         "JOIN gaiadr3.gaia_source AS g ON v.source_id = g.source_id "
         "WHERE v.best_class_name = 'CV'")
    fetch("gaia_cv_class.csv", "Gaia DR3 TAP vari_classifier_result join",
          lambda: tap(GAIA, q), "all 7306 DR3 CV-class sources")

    # 4. GUMS synthetic cones, same centres and radius.
    for dl, ra, dec in CONES:
        name = f"gums_dl{dl:+d}.csv"
        q = (f'SELECT Pop,Gmag,GBmag,GRmag,pmRA,pmDE FROM "VI/137/gum_mw" '
             f"WHERE CONTAINS(POINT('ICRS',RAICRS,DEICRS),"
             f"CIRCLE('ICRS',{ra},{dec},0.5))=1")
        fetch(name, "VizieR TAP VI/137/gum_mw", lambda q=q: tap(VIZIER, q),
              f"GUMS cone at l_c{dl:+d}, b_c")
        time.sleep(1.0)

    print("done")


if __name__ == "__main__":
    sys.exit(main())
