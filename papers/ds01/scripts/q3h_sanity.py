#!/usr/bin/env python3
"""Q3h: why did the HEASARC cones return zero rows? Sanity-test the coordinate columns."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocslib import tap_vot


def q(label, adql, maxrows=5):
    st, txt, dt, rows = tap_vot("heasarc", adql, timeout=300)
    n = "ERR" if rows is None else len(rows)
    print(f"[{label}] status={st} rows={n}")
    if rows is None:
        i = txt.find("QUERY_STATUS")
        print("    ERR:", txt[i:i + 200].replace("\n", " ") if i >= 0 else txt[:150])
    else:
        for r in rows[:maxrows]:
            print("    ", str(r)[:220])
    return rows


q("count swift2sxps", "SELECT COUNT(*) AS n FROM swift2sxps")
q("count swift2sxps dec<-47", "SELECT COUNT(*) AS n FROM swift2sxps WHERE dec < -47.0")
q("top5 swift2sxps dec<-47", "SELECT TOP 5 name,ra,dec FROM swift2sxps WHERE dec < -47.0")
q("count chanmaster", "SELECT COUNT(*) AS n FROM chanmaster")
q("count xmmmaster", "SELECT COUNT(*) AS n FROM xmmmaster")
q("xmmmaster near omega cen", "SELECT TOP 5 * FROM xmmmaster WHERE ra BETWEEN 201.0 AND 202.0 AND dec BETWEEN -47.6 AND -46.5")
q("chanmaster near omega cen", "SELECT TOP 5 * FROM chanmaster WHERE ra BETWEEN 201.0 AND 202.0 AND dec BETWEEN -47.6 AND -46.5")
q("count rosatlog", "SELECT COUNT(*) AS n FROM rosatlog")
q("rosatlog near omega cen", "SELECT TOP 5 * FROM rosatlog WHERE ra BETWEEN 201.0 AND 202.0 AND dec BETWEEN -47.6 AND -46.5")
q("count galexlog", "SELECT COUNT(*) AS n FROM galexlog")
q("galexlog near omega cen", "SELECT TOP 5 * FROM galexlog WHERE ra BETWEEN 201.0 AND 202.0 AND dec BETWEEN -47.6 AND -46.5")
q("count swiftmastr", "SELECT COUNT(*) AS n FROM swiftmastr")
q("swiftmastr near omega cen", "SELECT TOP 5 * FROM swiftmastr WHERE ra BETWEEN 201.0 AND 202.0 AND dec BETWEEN -47.6 AND -46.5")
q("MASTER_TABLE.pos_small sanity", "SELECT TOP 5 * FROM MASTER_TABLE.pos_small WHERE ra BETWEEN 201.0 AND 202.0 AND dec BETWEEN -47.6 AND -46.5")
