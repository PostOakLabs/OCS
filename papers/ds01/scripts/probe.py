#!/usr/bin/env python3
"""D27 connectivity probe: anonymous TAP/HTTP reachability for the DS-01 archival sweep.

Stdlib only (urllib). Prints one line per endpoint: NAME  STATUS  DETAIL
No logins, no tokens, no cookies.
"""
import urllib.request
import urllib.parse
import ssl
import sys

TIMEOUT = 45
CTX = ssl.create_default_context()

TAP = {
    "gaia": "https://gea.esac.esa.int/tap-server/tap/sync",
    "vizier": "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync",
    "heasarc": "https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync",
    "eso": "https://archive.eso.org/tap_obs/sync",
    "casda": "https://casda.csiro.au/casda_vo_tools/tap/sync",
    "datalab": "https://datalab.noirlab.edu/tap/sync",
    "mast": "https://mast.stsci.edu/vo/tap/sync",
    "irsa": "https://irsa.ipac.caltech.edu/TAP/sync",
    "cadc": "https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/tap/sync",
    "gemini": "https://archive.gemini.edu/tap/sync",
    "nrao": "https://data.nrao.edu/tap/sync",
    "simbad": "https://simbad.cds.unistra.fr/simbad/sim-tap/sync",
}

PLAIN = {
    "vizier_tsv": "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=I/355/gaiadr3&-c=201.41849%20-47.05715&-c.rs=2",
    "heasarc_browse": "https://heasarc.gsfc.nasa.gov/cgi-bin/W3Browse/w3query.pl",
    "nasa_ads_home": "https://ui.adsabs.harvard.edu/",
    "arxiv_api": "http://export.arxiv.org/api/query?search_query=all:pulsar&max_results=1",
    "ukssdc_2sxps": "https://www.swift.ac.uk/2SXPS/",
    "nsc_dr2_doc": "https://datalab.noirlab.edu/data/nscdr2",
    "atlas_api": "https://fallingstar-data.com/forcedphot/queue/",
    "ztf_irsa": "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query",
    "casda_web": "https://casda.csiro.au/casda_vo_tools/sia2/query",
    "parkes_dap": "https://dap.nci.org.au/",
    "sarao": "https://archive.sarao.ac.za/",
    "fssc_lat": "https://fermi.gsfc.nasa.gov/ssc/data/access/lat/",
    "chandra_csc": "https://cxc.harvard.edu/csc/",
    "noirlab_archive": "https://astroarchive.noirlab.edu/api/adv_search/find/?outfields=ra,dec&limit=1",
    "eso_saada": "https://archive.eso.org/wdb/wdb/eso/eso_archive_main/query",
    "gemini_web": "https://archive.gemini.edu/searchform",
    "sao_archive": "https://simbad.cds.unistra.fr/",
    "desi_spectro": "https://data.desi.lbl.gov/public/",
    "lamost_dr": "http://www.lamost.org/dr10/v2.0/",
    "ssa_uk": "https://www.eso.org/",
    "neowise": "https://irsa.ipac.caltech.edu/Missions/wise.html",
    "gator_ztf": "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-scan",
    "xmm_ssc": "https://www.cosmos.esa.int/web/xmm-newton/xsa",
    "erosita_dr1": "https://erosita.mpe.mpg.de/dr1/",
}


def head(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ocs-d27/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, str(r.headers.get("Content-Type", ""))[:60]
    except Exception as e:
        return "ERR", type(e).__name__ + ": " + str(e)[:110]


def tap(endpoint, adql, fmt="csv"):
    data = urllib.parse.urlencode(
        {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": fmt, "QUERY": adql}
    ).encode()
    req = urllib.request.Request(endpoint, data=data, headers={"User-Agent": "ocs-d27/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
            body = r.read(4000).decode("utf-8", "replace")
            return r.status, body.replace("\n", " | ")[:200]
    except Exception as e:
        return "ERR", type(e).__name__ + ": " + str(e)[:110]


if __name__ == "__main__":
    print("=== TAP sync (SELECT 1) ===")
    for name, ep in TAP.items():
        st, det = tap(ep, "SELECT TOP 1 1 AS one FROM TAP_SCHEMA.tables" if name == "vizier" else "SELECT 1 AS one")
        print(f"{name:10s} {str(st):5s} {det}")
    print("=== plain HTTP GET ===")
    for name, url in PLAIN.items():
        st, det = head(url)
        print(f"{name:16s} {str(st):5s} {det}")
