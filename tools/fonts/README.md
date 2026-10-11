# Profile typography

**Space Grotesk** supplies the display headings and large metrics. **Inter** supplies descriptions, buttons, chart labels and small captions.

Both families come from the official [Google Fonts repository](https://github.com/google/fonts), under the SIL Open Font License 1.1. The original licenses are included beside `manifest.json`, which records a pinned revision, source URLs and SHA-256 hashes. The font binaries are cached locally and excluded from Git.

To rebuild the artwork, install `tools/requirements.txt` and run `python tools/build_assets.py` from the repository root. Missing font files are downloaded from the pinned sources and checked against their hashes.

The generated SVGs contain glyph outlines and accessible image descriptions. Visitors do not need to install either font or allow external font loading.
