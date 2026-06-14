# Bundled uv (offline, all platforms)

These are the official Astral `uv` release tarballs (uv 0.11.21) for the supported
platforms. The plugin's uv resolver (`recall::_uv_from_bundle` in
searxng) extracts the one matching the host into the plugin data dir,
so first run works **without internet** on any of these targets — uv then brings its
own Python ≥3.10. This is deliberately heavier-but-compatible (see the compatibility
policy): the plugin self-provisions its whole runtime instead of assuming the host has uv.

Refresh: re-download from https://github.com/astral-sh/uv/releases for a new version.
