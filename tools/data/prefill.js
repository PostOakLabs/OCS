/**
 * prefill.js — Omega Centauri Society
 * Reads #in=<base64url-encoded JSON> from the URL hash and calls
 * window.OCS_APPLY_PREFILL(obj) if the host tool defines that function.
 *
 * Usage (add to any OCS tool page, after measurements.js):
 *   <script src="data/prefill.js"></script>
 *
 * Tools opt in by defining window.OCS_APPLY_PREFILL before this script runs
 * (or this script retries on DOMContentLoaded). If the function isn't defined
 * or the hash is absent/malformed, this script is silent.
 */
(function () {
  function base64urlDecode(s) {
    // base64url → base64 → binary → string
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    var pad = s.length % 4;
    if (pad) s += '===='.slice(pad);
    return atob(s);
  }

  function tryApply() {
    var hash = location.hash || '';
    var m = hash.match(/[#&]in=([A-Za-z0-9+/=_-]+)/);
    if (!m) return;
    var obj;
    try { obj = JSON.parse(base64urlDecode(m[1])); } catch (e) { return; }
    if (typeof window.OCS_APPLY_PREFILL === 'function') {
      window.OCS_APPLY_PREFILL(obj);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', tryApply);
  } else {
    tryApply();
  }
})();
