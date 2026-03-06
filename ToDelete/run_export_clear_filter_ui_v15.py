import importlib, io, csv, os, json, sys, time, pathlib
from datetime import datetime as dt
from flask import request, make_response, send_from_directory

def log(msg):
    now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[wrapv15] {now} {msg}", file=sys.stdout, flush=True)

# -------- Import user's app --------
CANDIDATES = ["lumaserver", "lumaServer", "lumaServer_merged", "server", "app"]
APP = None
mod = None
for name in CANDIDATES:
    try:
        mod = importlib.import_module(name)
        APP = None
        for attr in ("APP","app","application"):
            APP = getattr(mod, attr, None)
            if APP: 
                chosen_attr = attr
                break
        if APP:
            log(f"using app from {name}.{chosen_attr}")
            break
        if hasattr(mod, "create_app"):
            APP = mod.create_app()
            log(f"using app from {name}.create_app()")
            break
    except Exception as e:
        log(f"skip {name}: {e!r}")
if APP is None:
    raise RuntimeError("Could not import a Flask app from known module names.")

INDEX_FILE = None
for p in [pathlib.Path("index.html"), pathlib.Path("ui/index.html"), pathlib.Path("static/index.html")]:
    if p.exists():
        INDEX_FILE = p
        break
if INDEX_FILE:
    log(f"index path: {INDEX_FILE}")

FIELDS = ["ip","mac","hostname","dante_name","dante_ip","dante_mac","type","role","model","firmware","serialnumber","status"]  # Removed: version, status_ts (firmware duplicates version)
FW_FILTER = {"value": ""}

def _normalize_rows(payload):
    if not payload: return []
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("units"), list):
            return [r for r in payload["units"] if isinstance(r, dict)]
        if isinstance(payload.get("rows"), list):
            return [r for r in payload["rows"] if isinstance(r, dict)]
        return [v for v in payload.values() if isinstance(v, dict)]
    return []

def _desired_role_from_fw(name: str):
    n = (name or "").lower()
    if not n: return ""
    if any(k in n for k in ("-e4"," e4","-111","-112","-512","encoder","e4111")): return "encoder"
    if any(k in n for k in ("-d4"," d4","-121","-122","-521","decoder","d4511")): return "decoder"
    return ""

def _apply_fw_filter(rows):
    want_role = _desired_role_from_fw(FW_FILTER["value"])
    if not want_role: return rows
    out = []
    for r in rows:
        role = (r.get("type") or r.get("role") or "").strip().lower()
        model = (r.get("model") or "").lower()
        if role:
            if role == want_role: out.append(r)
        else:
            if want_role == "decoder" and "d4111" in model: out.append(r)
            if want_role == "encoder" and "e4211" in model: out.append(r)
    return out

def _download_csv_payload(rows):
    import io, csv
    out = io.StringIO()
    w = csv.writer(out, quoting=csv.QUOTE_ALL)
    w.writerow(FIELDS)
    for r in rows:
        row_values = []
        for k in FIELDS:
            if k == "firmware":
                # Prefer firmware; fallback to version if firmware missing
                v = r.get("firmware") or r.get("version") or ""
            elif k == "serialnumber":
                # Prepend tab to force Excel to treat as text
                v = r.get(k, "")
                if v and str(v).strip():
                    v = "\t" + str(v)
            else:
                v = r.get(k, "")
            row_values.append(v)
        w.writerow(row_values)
    return out.getvalue().encode("utf-8")

def _build_csv_response(content: bytes, filename="units.csv"):
    resp = make_response(content)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp.headers["Cache-Control"] = "no-store"
    return resp

# -------------------- extra endpoints (unique endpoint names) -----------------

@APP.get("/fw-filter.js", endpoint="wrap_fw_js")
def _serve_fw_js():
    return """
    (function(){
      window.__fwFilter = {
        get: function(){ try { return document.cookie.split('; ').find(x=>x.startsWith('fw_filter='))?.split('=')[1] || ''; } catch(e){ return ''; } },
        set: function(v){ try { document.cookie = 'fw_filter=' + (v||'') + '; path=/; max-age=604800'; } catch(e){} }
      };
      console.log('[fw] helper online');
    })();
    """, 200, {"Content-Type":"application/javascript; charset=utf-8", "Cache-Control":"no-store"}

def _serve_index_with_script_tag():
    if not INDEX_FILE:
        return "UI missing (index.html not found)", 404
    return send_from_directory(INDEX_FILE.parent.as_posix(), INDEX_FILE.name)

def hard_hijack_root_and_export():
    @APP.get("/", endpoint="wrap_root_index")
    def _root():
        return _serve_index_with_script_tag()

    @APP.post("/api/set_fw_filter", endpoint="wrap_set_fw_filter")
    def set_fw_filter():
        try:
            data = request.get_json(silent=True) or {}
            FW_FILTER["value"] = (data.get("value") or "").strip()
            resp = make_response({"ok": True, "value": FW_FILTER["value"]})
            resp.set_cookie("fw_filter", FW_FILTER["value"], max_age=7*24*3600, httponly=False, samesite="Lax")
            return resp
        except Exception as e:
            return {"ok": False, "error": str(e)}, 400

    @APP.get("/api/fw_dbg", endpoint="wrap_fw_dbg")
    def fw_dbg():
        return {"fw_filter": FW_FILTER["value"]}

    @APP.get("/api/download_csv", endpoint="wrap_download_csv_get")
    def compat_download_csv():
        try:
            cache_units = getattr(mod, "cache_units", {})
            rows = list(cache_units.values()) if isinstance(cache_units, dict) else []
        except Exception:
            rows = []
        rows = _apply_fw_filter(rows)
        content = _download_csv_payload(rows)
        fn = f"units_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return _build_csv_response(content, fn)

    # Match what the UI calls
    @APP.post("/api/export_csv", endpoint="wrap_export_csv_post")
    def export_csv_post():
        try:
            cache_units = getattr(mod, "cache_units", {})
            rows = list(cache_units.values()) if isinstance(cache_units, dict) else []
        except Exception:
            rows = []
        rows = _apply_fw_filter(rows)
        content = _download_csv_payload(rows)
        fn = f"units_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return _build_csv_response(content, fn)

hard_hijack_root_and_export()

# -------------------- run the server --------------------

if __name__ == "__main__":
    port = int(os.environ.get("LUMA_PORT", "8088"))
    log(f"=== Wrapper v15 (index passthrough + export) http://127.0.0.1:{port} ===")
    log(" * Serving Flask app (imported)")
    log(" * Debug mode: off")
    try:
        APP.run(host="0.0.0.0", port=port, debug=False, threaded=True)
    except Exception as e:
        log(f"server error: {e!r}")
