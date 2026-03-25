import streamlit as st
from pathlib import Path

st.set_page_config(page_title="About — VeriLite", layout="wide")

assets_dir = Path(__file__).parent.parent / "assets"
logo_path = assets_dir / "setu_logo.png" 

col1, col2 = st.columns([1, 4], vertical_alignment="center")

with col1:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)

with col2:
    st.title("About VeriLite")

    source_url = "https://github.com/theopakieser/FinalYearProject2026"
    st.markdown(f"**Source code:** {source_url}")

    st.link_button("Open repository", source_url)

st.divider()

st.markdown(
    """
VeriLite is a lightweight file integrity verification tool designed for educational and forensic-style workflows.
It creates a trusted baseline of a directory, then verifies that baseline later to detect file tampering.

The goal is simple: **make integrity checking understandable, auditable, and fast** — without heavyweight enterprise tooling.
"""
)

st.subheader("Core workflow")
st.markdown(
    """
1. **Scan** a target directory  
2. **Hash** files (default: SHA-256; optional legacy: MD5/SHA-1)  
3. **Create baseline** (JSON manifest + signature for tamper-evidence)  
4. **Verify baseline** (detect **modified / added / deleted** files)  
5. **Explain changes** for supported formats using **text snapshots** and **chunk-based location**
"""
)

st.subheader("Key features")
st.markdown(
    """
- **Directory scanning** (recursive)
- **Cryptographic hashing** (SHA-256 default; MD5/SHA-1 supported for comparison)
- **Baseline manifest (JSON)** containing file metadata and hashes
- **Baseline signing** (`.sig`) to detect baseline tampering
- **Integrity verification** with modified/added/deleted reporting
- **Text snapshot extraction** for supported types (e.g., `.txt`, `.csv`, `.json`, `.md`)
- **Chunk-based change localisation** (e.g., “changed in chunk 3 → ~lines 61–80”)
- **Streamlit GUI** to explore reports and view baseline vs current snapshot chunks side-by-side
"""
)

st.subheader("Change highlighting approach (v1)")
st.markdown(
    """
To satisfy “show what changed and where” within time constraints, VeriLite uses a **chunk-based** approach:

- Extracts normalised text for supported files
- Splits text into fixed-size chunks (e.g., 20 lines per chunk)
- Compares baseline chunk hashes to current chunk hashes
- Reports the **chunk indices** that changed, which map to approximate line ranges

This is fast and simple, and works well for educational demonstration.
"""
)

st.subheader("Limitations")
st.markdown(
    """
- **Binary files**: VeriLite can detect changes (hash mismatch) but cannot explain *what* changed.
- **PDFs**: if a PDF has no extractable text (scanned/image-only), text snapshot diffing may be unavailable.
- **Normalisation**: text snapshots may normalise certain whitespace/newline patterns to reduce noise.
"""
)

st.subheader("Outputs")
st.markdown(
    """
- `baseline.json` — baseline manifest
- `baseline.sig` — signature hash for tamper-evidence
- `baseline.report.json` — verification report used by the GUI
- `snapshots_baseline/` — baseline text snapshots
- `snapshots_current/` — current verification run snapshots
"""
)

st.subheader("Technologies")
st.markdown(
    """
- Python
- JSON manifests
- SHA-256 hashing (plus optional MD5/SHA-1)
- Streamlit GUI
"""
)
