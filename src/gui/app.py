import json
import html
import tempfile
import zipfile
from pathlib import Path, PureWindowsPath
from typing import Optional

import pandas as pd
import streamlit as st


st.set_page_config(page_title="VeriLite GUI", layout="wide")

# ---- CSS ----
st.markdown(
    """
<style>
.diffbox {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.9rem;
  line-height: 1.35;
  white-space: pre;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.04);
  overflow-x: auto;
}

.same-line {
  display: block;
  padding: 0 6px;
  border-radius: 6px;
  margin: 1px 0;
  background: rgba(34, 197, 94, 0.16);   /* green */
  border-left: 4px solid rgba(34, 197, 94, 0.65);
}

.diff-line {
  display: block;
  padding: 0 6px;
  border-radius: 6px;
  margin: 1px 0;
  background: rgba(239, 68, 68, 0.16);   /* red */
  border-left: 4px solid rgba(239, 68, 68, 0.65);
}

.lineno {
  display: inline-block;
  width: 64px;
  color: rgba(255,255,255,0.45);
  user-select: none;
}

.missing {
  color: rgba(255,255,255,0.45);
  font-style: italic;
}
</style>
""",
    unsafe_allow_html=True
)

# ---- Sidebar branding ----
assets_dir = Path(__file__).parent / "assets"
logo_path = assets_dir / "setu_logo.png"

with st.sidebar:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)

    st.markdown("### VeriLite")
    st.caption("Lightweight file integrity checker for baseline + verification, with chunk-based change localisation.")

    source_url = "https://github.com/theopakieser/FinalYearProject2026"
    st.markdown(f"Source code: {source_url}")
    st.link_button("Open repository", source_url)

    st.divider()


# ---- Helpers ----
def load_report(report_path: Path) -> dict:
    return json.loads(report_path.read_text(encoding="utf-8"))


def chunk_bounds(idx: int, max_lines: int) -> tuple[int, int]:
    start = idx * max_lines + 1
    end = start + max_lines - 1
    return start, end


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_into_chunks(text: str, max_lines: int) -> list[str]:
    # splitlines(), then join in groups of max_lines, strip each chunk
    lines = text.splitlines()
    chunks = []
    for i in range(0, len(lines), max_lines):
        chunk = "\n".join(lines[i:i + max_lines]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def render_colored_lines(left_text: str, right_text: str, start_line: int) -> tuple[str, str]:
    """
    Returns (left_html, right_html) where each line is colored:
    - green if equal at same line index
    - red if different / missing on either side
    """
    left_lines = left_text.splitlines()
    right_lines = right_text.splitlines()

    n = max(len(left_lines), len(right_lines))
    left_out = []
    right_out = []

    for i in range(n):
        ln = start_line + i

        l = left_lines[i] if i < len(left_lines) else None
        r = right_lines[i] if i < len(right_lines) else None

        same = (l == r) and (l is not None)

        left_class = "same-line" if same else "diff-line"
        right_class = "same-line" if same else "diff-line"

        l_text = html.escape(l) if l is not None else '<span class="missing">[no line]</span>'
        r_text = html.escape(r) if r is not None else '<span class="missing">[no line]</span>'

        left_out.append(f'<span class="{left_class}"><span class="lineno">{ln:>4} |</span> {l_text}</span>')
        right_out.append(f'<span class="{right_class}"><span class="lineno">{ln:>4} |</span> {r_text}</span>')

    left_html = '<div class="diffbox">' + "\n".join(left_out) + "</div>"
    right_html = '<div class="diffbox">' + "\n".join(right_out) + "</div>"
    return left_html, right_html


# ---- ZIP handling for deployment ----
def extract_bundle_zip(uploaded_zip) -> Path:
    """
    Extract uploaded ZIP to a temp folder and return the extraction root Path.
    """
    tmp_root = Path(tempfile.gettempdir()) / "verilite_bundle"
    extract_root = tmp_root / Path(uploaded_zip.name).stem

    # wipe old extract (deterministic)
    if extract_root.exists():
        for p in sorted(extract_root.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            else:
                try:
                    p.rmdir()
                except OSError:
                    pass
        try:
            extract_root.rmdir()
        except OSError:
            pass

    extract_root.mkdir(parents=True, exist_ok=True)

    zip_path = extract_root / uploaded_zip.name
    zip_path.write_bytes(uploaded_zip.getvalue())

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_root)

    return extract_root


def resolve_snapshot_from_bundle(bundle_root: Path, snap_path_str: str):
    if not snap_path_str:
        return None

    # ff it's a Windows path, parse it correctly on Linux
    if "\\" in snap_path_str:
        name = PureWindowsPath(snap_path_str).name
    else:
        name = Path(snap_path_str).name

    # first try the expected bundle layout
    for folder in ["snapshots_baseline", "snapshots_current"]:
        root = bundle_root / folder
        if root.exists():
            hits = list(root.rglob(name))  #recursive (supports nested)
            if hits:
                return hits[0]

    #fallback: search anywhere in bundle
    hits = list(bundle_root.rglob(name))
    return hits[0] if hits else None


def build_modified_df(report: dict) -> pd.DataFrame:
    rows = []
    for item in report.get("modified", []):
        ci = item.get("chunk_info") or {}
        rows.append({
            "path": item.get("path"),
            "raw_changed": item.get("raw_changed"),
            "text_changed": item.get("text_changed"),
            "chunks_changed": ci.get("changed", 0),
            "tamper_ratio": ci.get("tamper_ratio"),
        })
    return pd.DataFrame(rows)


def build_added_df(report: dict) -> pd.DataFrame:
    return pd.DataFrame({"path": report.get("added", [])})


def build_deleted_df(report: dict) -> pd.DataFrame:
    return pd.DataFrame({"path": report.get("deleted", [])})


# ---- App ----
st.title("VeriLite — Integrity Report Viewer")

st.sidebar.header("Load report")

mode = st.sidebar.radio(
    "Choose input method",
    ["Upload bundle (.zip)", "Upload report", "Browse folder", "Paste path"],
    index=0
)

report_file: Optional[Path] = None
bundle_root: Optional[Path] = None

if mode == "Upload bundle (.zip)":
    uploaded_zip = st.sidebar.file_uploader(
        "Upload VeriLite bundle (.zip)",
        type=["zip"],
        accept_multiple_files=False
    )
    if uploaded_zip is not None:
        bundle_root = extract_bundle_zip(uploaded_zip)

        reports = sorted(bundle_root.rglob("*.report.json"))
        if not reports:
            st.sidebar.error("No *.report.json found inside the ZIP.")
        else:
            chosen = st.sidebar.selectbox(
                "Select report inside bundle",
                options=[str(p.relative_to(bundle_root)) for p in reports],
                index=0
            )
            report_file = bundle_root / chosen
            st.sidebar.success(f"Loaded bundle: {uploaded_zip.name}")

elif mode == "Upload report":
    uploaded = st.sidebar.file_uploader(
        "Upload *.report.json",
        type=["json"],
        accept_multiple_files=False
    )
    if uploaded is not None:
        tmp_dir = Path(tempfile.gettempdir()) / "verilite_reports"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        tmp_path = tmp_dir / uploaded.name
        tmp_path.write_bytes(uploaded.getvalue())

        report_file = tmp_path
        st.sidebar.success(f"Loaded: {uploaded.name}")

elif mode == "Browse folder":
    folder_str = st.sidebar.text_input(
        "Folder to search",
        value=str(Path.cwd())
    ).strip()

    folder = Path(folder_str)
    if folder.exists() and folder.is_dir():
        reports = sorted(folder.rglob("*.report.json"))
        if reports:
            chosen = st.sidebar.selectbox(
                "Select report",
                options=[str(p) for p in reports],
                index=0
            )
            report_file = Path(chosen)
        else:
            st.sidebar.info("No *.report.json files found in this folder.")
    else:
        st.sidebar.warning("Folder not found.")

else:  # Paste path
    report_path_str = st.sidebar.text_input(
        "Report path (.report.json)",
        value=""
    ).strip()

    if report_path_str:
        rp = Path(report_path_str)
        if rp.exists() and rp.is_file():
            report_file = rp
        else:
            st.sidebar.error("That file path doesn't exist.")

# stop if nothing selected
if report_file is None:
    st.info("Load a report using the sidebar to begin.")
    st.stop()

report = load_report(report_file)
if report.get("schema_version") != 1 or "modified" not in report:
    st.error("That JSON doesn't look like a VeriLite report.")
    st.stop()

# header info
colA, colB, colC, colD = st.columns(4)
with colA:
    st.metric("Modified", report.get("summary", {}).get("modified", 0))
with colB:
    st.metric("Added", report.get("summary", {}).get("added", 0))
with colC:
    st.metric("Deleted", report.get("summary", {}).get("deleted", 0))
with colD:
    st.write("**Generated at**")
    st.write(report.get("generated_at", "unknown"))

with st.expander("Run details", expanded=False):
    st.write(f"**Algorithm:** {report.get('algorithm')}")
    st.write(f"**Folder:** {report.get('folder')}")
    st.write(f"**Baseline:** {report.get('baseline_path')}")
    st.write(f"**Report file:** {str(report_file)}")

# tabs
tab_mod, tab_added, tab_deleted = st.tabs(["Modified", "Added", "Deleted"])

# ---- MODIFIED FILES ----
with tab_mod:
    df_mod = build_modified_df(report)
    if df_mod.empty:
        st.success("No modified files in this report.")
        st.stop()

    st.subheader("Modified files")
    q = st.text_input("Filter by path contains", value="").strip().lower()

    df_show = df_mod.copy()
    if q:
        df_show = df_show[df_show["path"].str.lower().str.contains(q)]

    st.dataframe(df_show, use_container_width=True, hide_index=True)

    paths = df_show["path"].tolist()
    if not paths:
        st.warning("No files match your filter.")
        st.stop()

    chosen = st.selectbox("Select a file to inspect", options=paths, index=0)

    chosen_rec = None
    for item in report.get("modified", []):
        if item.get("path") == chosen:
            chosen_rec = item
            break

    if chosen_rec is None:
        st.error("Could not locate the selected file record in the report.")
        st.stop()

    st.divider()
    st.subheader("Change details")

    meta1, meta2 = st.columns(2)
    with meta1:
        st.write("**Baseline raw hash**")
        st.code(chosen_rec.get("baseline_raw", ""), language="text")
        st.write("**Current raw hash**")
        st.code(chosen_rec.get("current_raw", ""), language="text")
    with meta2:
        st.write("**Baseline text hash**")
        st.code(str(chosen_rec.get("baseline_text_hash", "")), language="text")
        st.write("**Current text hash**")
        st.code(str(chosen_rec.get("current_text_hash", "")), language="text")

    ci = chosen_rec.get("chunk_info") or {}
    max_lines = int(ci.get("max_lines", 20))
    changed_indices = ci.get("changed_indices", [])
    added_indices = ci.get("added_indices", [])
    removed_indices = ci.get("removed_indices", [])

    st.write("**Chunk change summary**")
    st.write({
        "max_lines": max_lines,
        "changed_indices": changed_indices,
        "added_indices": added_indices,
        "removed_indices": removed_indices,
        "tamper_ratio": ci.get("tamper_ratio"),
    })

    base_snap = chosen_rec.get("baseline_snapshot_path")
    curr_snap = chosen_rec.get("current_snapshot_path")

    if not base_snap or not curr_snap:
        st.warning(
            "Snapshot paths are missing in this report. "
            "Add baseline_snapshot_path/current_snapshot_path to your report output, then re-run verify."
        )
        st.stop()

# resolve snapshot paths (bundle upload vs local paths)
if bundle_root is not None:
    base_rel = chosen_rec.get("baseline_snapshot_rel")
    curr_rel = chosen_rec.get("current_snapshot_rel")

    if not base_rel or not curr_rel:
        st.error("This report bundle is missing snapshot relative paths (baseline_snapshot_rel/current_snapshot_rel). Re-run verify and re-zip.")
        st.stop()

    baseline_dir = bundle_root / "snapshots_baseline"
    current_dir = bundle_root / "snapshots_current"

    # handle bundles where folders are nested
    if not baseline_dir.exists():
        hits = [p for p in bundle_root.rglob("snapshots_baseline") if p.is_dir()]
        baseline_dir = hits[0] if hits else None

    if not current_dir.exists():
        hits = [p for p in bundle_root.rglob("snapshots_current") if p.is_dir()]
        current_dir = hits[0] if hits else None

    if baseline_dir is None or current_dir is None:
        st.error("Could not find snapshots_baseline/ and snapshots_current/ inside the uploaded ZIP.")
        st.stop()

    base_path = baseline_dir / base_rel
    curr_path = current_dir / curr_rel
else:
    base_path = Path(base_snap)
    curr_path = Path(curr_snap)

    if base_path is None or curr_path is None:
        st.error("Could not resolve snapshot paths from the uploaded bundle.")
        st.stop()

    if not base_path.exists() or not curr_path.exists():
        st.error(
            "Snapshot file(s) not found.\n\n"
            f"Baseline snapshot: {base_path}\n"
            f"Current snapshot: {curr_path}"
        )
        st.stop()

    base_text = read_text_file(base_path)
    curr_text = read_text_file(curr_path)

    base_chunks = split_into_chunks(base_text, max_lines=max_lines)
    curr_chunks = split_into_chunks(curr_text, max_lines=max_lines)

    if changed_indices:
        default_chunk = changed_indices[0]
    else:
        default_chunk = 0

    all_indices = sorted(set(changed_indices + added_indices + removed_indices))
    if not all_indices:
        n = max(len(base_chunks), len(curr_chunks))
        all_indices = list(range(n))

    chosen_chunk = st.selectbox(
        "Select chunk index",
        options=all_indices,
        index=all_indices.index(default_chunk) if default_chunk in all_indices else 0
    )

    start_line, end_line = chunk_bounds(chosen_chunk, max_lines)
    st.caption(f"Chunk {chosen_chunk} corresponds to lines ~{start_line}–{end_line} (max_lines={max_lines})")

    left, right = st.columns(2)

    base_chunk = base_chunks[chosen_chunk] if chosen_chunk < len(base_chunks) else ""
    curr_chunk = curr_chunks[chosen_chunk] if chosen_chunk < len(curr_chunks) else ""

    left_html, right_html = render_colored_lines(base_chunk, curr_chunk, start_line)

    st.markdown(
        "- **Green** = same line in baseline and current\n"
        "- **Red** = changed / added / removed line",
    )

    with left:
        st.write("**Baseline snapshot chunk**")
        st.markdown(left_html, unsafe_allow_html=True)

    with right:
        st.write("**Current snapshot chunk**")
        st.markdown(right_html, unsafe_allow_html=True)

# ---- ADDED FILES ----
with tab_added:
    df_added = build_added_df(report)
    st.subheader("Added files")
    if df_added.empty:
        st.success("No added files in this report.")
    else:
        st.dataframe(df_added, use_container_width=True, hide_index=True)

# ---- DELETED FILES ----
with tab_deleted:
    df_deleted = build_deleted_df(report)
    st.subheader("Deleted files")
    if df_deleted.empty:
        st.success("No deleted files in this report.")
    else:
        st.dataframe(df_deleted, use_container_width=True, hide_index=True)