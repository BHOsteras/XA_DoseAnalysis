# XA_DoseAnalysis

Analysis of radiation dose data from interventional procedures. The package
reads Excel exports from **DoseTrack** (dose data) and **IDS7** (procedure
data), cleans and merges them on accession number, maps free-text procedure
descriptions to standardized names, and produces representative-dose
statistics, plots, trend analyses and DRL comparisons.

## Setup

The project is managed with [uv](https://docs.astral.sh/uv/):

```bash
uv sync          # create the environment and install dependencies
uv run pytest    # run the test suite
uv run ruff check . && uv run ruff format .   # lint and format
```

## Configuration

Everything machine- and analysis-specific lives in [`config.toml`](config.toml):

- **`[paths.data_root]`** — where the Excel exports live, per machine
  (keyed by hostname, with a `default` fallback).
- **`[room_aliases]`** — room-name variants that are normalized on import
  (e.g. `KRH_XA3_Coroventis` → `KRH_XA3`).
- **`[analyses.<name>]`** — one block per analysis: the rooms to include,
  which mapping dictionary to use, an optional age limit, and the procedures
  to plot/report with their y-axis limits and optional diagnostic reference
  levels (`drl_dap`, `drl_cak`).

The expected data layout is `<data_root>/<subfolder>/<year>/*.xlsx`, with
subfolders for IDS7, procedure-level DoseTrack ("Serienivå") and
exposure-level DoseTrack ("Eksponeringsnivå") exports. The DoseTrack export
may be pre-filtered to `Ordinal = 1` in Excel (smaller files) or not — the
pipeline filters in code either way.

**Privacy:** the IDS7 export must not contain the `Fødselsnummer` column;
the pipeline refuses to run if it is present. For duplicate detection, add an
anonymized `Pasient` column instead.

## Usage

The notebooks in [`notebooks/`](notebooks/) are thin front-ends:

| Notebook | Purpose |
| --- | --- |
| `representative_doses.ipynb` | Boxplots + summary statistics per procedure/lab, DRL comparison, Excel export |
| `trends.ipynb` | Dose trends per month/quarter/year |
| `angle_heatmaps.ipynb` | Air kerma by C-arm angle (exposure-level data) |
| `data_quality.ipynb` | Pipeline quality report and examination-code lists |

A complete analysis is a handful of calls:

```python
import xa_dose_analysis as xa

xa.setup_logging("INFO")
cfg = xa.load_config()

ds = xa.load_dataset(cfg, year=2025)        # read + clean + merge
pci = xa.select_analysis(ds, cfg, "pci")    # room filter + procedure mapping

xa.plot_representative_doses(pci, cfg.analysis("pci"))
stats = xa.summary_by_procedure(pci)
xa.compare_with_drl(stats, cfg.analysis("pci"))
xa.export_summary({"PCI 2025": stats}, cfg.reports_dir / "pci_2025.xlsx")
ds.quality.to_frame()                       # data-quality overview
```

## Package layout

| Module | Purpose |
| --- | --- |
| `columns.py` | **All** column names of the export formats — edit here if an export changes |
| `config.py` | Loads `config.toml` |
| `io.py` | Excel import, Ordinal filtering, privacy guard |
| `cleaning.py` | IDS7 filters, accession validation/correction, room standardization |
| `merging.py` | Per-accession aggregation and the IDS7–DoseTrack merge |
| `mapping.py` + `mapping_dicts/` | Procedure-description mapping (criteria syntax: `' & '`, `'~'` = exclude) |
| `pipeline.py` | High-level API: `load_dataset`, `select_analysis`, … |
| `reporting.py` | Summary statistics, pretty-printing, Excel export |
| `plotting.py` | Boxplots and angle heatmaps |
| `trends.py` | Dose trends over time |
| `drl.py` | Diagnostic reference level comparison |
| `quality.py` | Data-quality report |

The old notebooks (with their executed outputs) are kept in
[`notebooks/archive/`](notebooks/archive/) as a historical record and as the
reference for verifying the refactored pipeline.
