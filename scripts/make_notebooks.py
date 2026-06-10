"""One-off helper that generates the analysis notebooks in notebooks/.

Run with: uv run python scripts/make_notebooks.py
"""

import json
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def write_notebook(name: str, cells: list[dict]) -> None:
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = NOTEBOOKS_DIR / name
    path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


SETUP = """\
%load_ext autoreload
%autoreload 2

import xa_dose_analysis as xa

xa.setup_logging("INFO")  # use "WARNING" for less output
cfg = xa.load_config()"""


representative_doses = [
    md(
        "# Representative doses\n"
        "\n"
        "Boxplots and summary statistics of DAP/CAK/exposure time per procedure and lab.\n"
        "\n"
        "Set `ANALYSIS` to one of the analyses in `config.toml` "
        "(`pci`, `elfys`, `radiology`, `dsa`, `pediatric`) and `YEAR` to the year to analyse — "
        "a single year (`2025`), a list (`[2023, 2024, 2025]`), or `None` to read every year "
        "under the data folders."
    ),
    code(SETUP),
    code('ANALYSIS = "pci"\nYEAR = 2025  # a single year, a list like [2023, 2024], or None for all years'),
    code(
        "# Read, clean and merge the IDS7 and DoseTrack exports:\n"
        "ds = xa.load_dataset(cfg, year=YEAR)\n"
        "ds.quality.to_frame()"
    ),
    code(
        "# Filter to the rooms of the analysis and map the procedure descriptions:\n"
        "data = xa.select_analysis(ds, cfg, ANALYSIS)\n"
        "data.head()"
    ),
    code(
        "# Which descriptions were not recognized by the mapping?\n"
        "ds.quality.unmapped_descriptions[ANALYSIS].head(20)"
    ),
    code(
        "# Boxplot per configured procedure (save=True writes PNGs to the Figures folder):\n"
        "xa.plot_representative_doses(data, cfg.analysis(ANALYSIS), save=False)"
    ),
    code(
        "# Summary statistics (median, bootstrap 95% CI, IQR, range) per procedure and room:\n"
        "stats = xa.summary_by_procedure(data, seed=1)\n"
        "xa.print_summary(stats)\n"
        "stats"
    ),
    code(
        "# Compare against the diagnostic reference levels configured in config.toml:\n"
        "xa.compare_with_drl(stats, cfg.analysis(ANALYSIS))"
    ),
    code(
        "# Export the statistics to Excel:\n"
        'xa.export_summary({f"{ANALYSIS} {YEAR}": stats}, cfg.reports_dir / f"{ANALYSIS}_{YEAR}.xlsx")'
    ),
]

trends = [
    md(
        "# Dose trends over time\n"
        "\n"
        "Median and IQR of DAP per month/quarter/year, per procedure.\n"
        "Reads all years under the data folders when `YEAR = None`."
    ),
    code(SETUP),
    code(
        'ANALYSIS = "pci"\nYEAR = None  # None = all years in the data folders\nFREQ = "Q"  # "M", "Q" or "Y"'
    ),
    code("ds = xa.load_dataset(cfg, year=YEAR)\ndata = xa.select_analysis(ds, cfg, ANALYSIS)"),
    code(
        "# Trend plot per configured procedure (with its DRL when configured):\n"
        "for procedure in cfg.analysis(ANALYSIS).procedures:\n"
        "    xa.plot_trend(data, procedure.name, freq=FREQ, drl=procedure.drl_dap, save=False)"
    ),
    code(
        "# The numbers behind one of the plots:\n"
        "procedure = cfg.analysis(ANALYSIS).procedures[0].name\n"
        "xa.trend_table(data, procedure, freq=FREQ)"
    ),
    code('# Per-room trends for one procedure:\nxa.trend_table(data, procedure, freq="Y", by_room=True)'),
]

angle_heatmaps = [
    md(
        "# Air kerma by C-arm angle\n"
        "\n"
        "Heatmaps of where the dose is delivered in the LAO/RAO x cranial/caudal angle plane,\n"
        "from exposure-level DoseTrack exports.\n"
        "\n"
        "The exposure-level files are large; the combined data is cached as a pickle file in the\n"
        "data folder, so only the first run is slow."
    ),
    code(SETUP),
    code('ANALYSIS = "pci"\nYEAR = 2025\nBIN_SIZE = 10  # degrees'),
    code(
        "# Procedure-level data for grouping the exposures by mapped procedure:\n"
        "ds = xa.load_dataset(cfg, year=YEAR)\n"
        "data = xa.select_analysis(ds, cfg, ANALYSIS)"
    ),
    code(
        "# Exposure-level data (cached after the first run):\n"
        "exposures = xa.load_exposure_data(cfg, year=YEAR)\n"
        "len(exposures)"
    ),
    code(
        "for procedure in cfg.analysis(ANALYSIS).procedures:\n"
        "    proc_exposures = xa.filter_exposures_for_procedure(exposures, data, procedure.name)\n"
        "    xa.plot_air_kerma_angle_heatmap(proc_exposures, procedure.name, bin_size=BIN_SIZE, save=False)"
    ),
]

data_quality = [
    md(
        "# Data quality\n"
        "\n"
        "Structured overview of the data pipeline for one period: rows removed per filter,\n"
        "how well IDS7 and DoseTrack matched, corrected duplicates, and unmapped procedures\n"
        "per analysis."
    ),
    code(SETUP),
    code("YEAR = 2025"),
    code("ds = xa.load_dataset(cfg, year=YEAR)\nds.quality.to_frame()"),
    code(
        "# Run the analyses to collect their unmapped procedure descriptions:\n"
        'for name in ["pci", "elfys", "radiology", "dsa"]:\n'
        "    xa.select_analysis(ds, cfg, name)\n"
        "ds.quality.to_frame()"
    ),
    code(
        "# The full report (counters, invalid accessions, unmapped descriptions) as Excel:\n"
        'ds.quality.to_excel(cfg.reports_dir / f"data_quality_{YEAR}.xlsx")'
    ),
    code(
        "# Examination-code lists per lab, for discussing which procedures to report on:\n"
        "xa.export_examination_codes(ds.merged, cfg.reports_dir)"
    ),
]

write_notebook("representative_doses.ipynb", representative_doses)
write_notebook("trends.ipynb", trends)
write_notebook("angle_heatmaps.ipynb", angle_heatmaps)
write_notebook("data_quality.ipynb", data_quality)
