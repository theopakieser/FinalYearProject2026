import json
from pathlib import Path

import pandas as pd
import streamlit as st
import tempfile

st.set_page_config(page_title="VeriLite GUI", layout="wide")

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


def load_report(report_path: Path) -> dict:
    return json.loads(report_path.read_text(encoding="utf-8"))


def chunk_bounds(idx: int, max_lines: int) -> tuple[int, int]:
    start = idx * max_lines + 1
    end = start + max_lines - 1
    return start, end


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_into_chunks(text: str, max_lines: int) -> list[str]:
    #splitlines(), then join in groups of max_lines, strip each chunk
    lines = text.splitlines()
    chunks = []
    for i in range(0, len(lines), max_lines):
        chunk = "\n".join(lines[i:i + max_lines]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


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


st.title("VeriLite — Integrity Report Viewer")

st.sidebar.header("Load report")

mode = st.sidebar.radio(
    "Choose input method",
    ["Upload report", "Browse folder", "Paste path"],
    index=0
)

report_file = None

if mode == "Upload report":
    uploaded = st.sidebar.file_uploader(
        "Upload *.report.json",
        type=["json"],
        accept_multiple_files=False
    )

    if uploaded is not None:
        #save upload to a temp file so the rest of the app can treat it like a normal Path
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

else:  #paste path
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

#stop if nothing selected
if report_file is None:
    st.info("Load a report using the sidebar to begin.")
    st.stop()

report = load_report(report_file)
if report.get("schema_version") != 1 or "modified" not in report:
    st.error("That JSON doesn't look like a VeriLite report.")
    st.stop()

#header info
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

#tabs
tab_mod, tab_added, tab_deleted = st.tabs(["Modified", "Added", "Deleted"])

#----MODIFIED FILES----
with tab_mod:
    df_mod = build_modified_df(report)
    if df_mod.empty:
        st.success("No modified files in this report.")
        st.stop()

    #filters
    st.subheader("Modified files")
    q = st.text_input("Filter by path contains", value="").strip().lower()

    df_show = df_mod.copy()
    if q:
        df_show = df_show[df_show["path"].str.lower().str.contains(q)]

    st.dataframe(df_show, use_container_width=True, hide_index=True)

    #pick one file to inspect
    paths = df_show["path"].tolist()
    if not paths:
        st.warning("No files match your filter.")
        st.stop()

    chosen = st.selectbox("Select a file to inspect", options=paths, index=0)

    #find full record
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

    #snapshot paths
    base_snap = chosen_rec.get("baseline_snapshot_path")
    curr_snap = chosen_rec.get("current_snapshot_path")

    if not base_snap or not curr_snap:
        st.warning(
            "Snapshot paths are missing in this report. "
            "Add baseline_snapshot_path/current_snapshot_path to your report output, then re-run verify."
        )
        st.stop()

    base_path = Path(base_snap)
    curr_path = Path(curr_snap)

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

    #choose which chunk to view
    if changed_indices:
        default_chunk = changed_indices[0]
    else:
        default_chunk = 0

    all_indices = sorted(set(changed_indices + added_indices + removed_indices))
    if not all_indices:
        #fallback: allow user to browse chunk 0..N-1
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
    with left:
        st.write("**Baseline snapshot chunk**")
        chunk_text = base_chunks[chosen_chunk] if chosen_chunk < len(base_chunks) else ""
        st.code(chunk_text, language="text")
    with right:
        st.write("**Current snapshot chunk**")
        chunk_text = curr_chunks[chosen_chunk] if chosen_chunk < len(curr_chunks) else ""
        st.code(chunk_text, language="text")


#----ADDED FILES----
with tab_added:
    df_added = build_added_df(report)
    st.subheader("Added files")
    if df_added.empty:
        st.success("No added files in this report.")
    else:
        st.dataframe(df_added, use_container_width=True, hide_index=True)

#----DELETED FILES----
with tab_deleted:
    df_deleted = build_deleted_df(report)
    st.subheader("Deleted files")
    if df_deleted.empty:
        st.success("No deleted files in this report.")
    else:
        st.dataframe(df_deleted, use_container_width=True, hide_index=True)