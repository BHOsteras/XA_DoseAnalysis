"""Analysis of radiation dose data from interventional procedures.

The package reads Excel exports from DoseTrack (dose data) and IDS7
(procedure data), cleans and merges them, maps procedure descriptions to
standardized names, and produces representative-dose statistics and plots.

Typical use in a notebook:

    import xa_dose_analysis as xa

    xa.setup_logging("INFO")
    cfg = xa.load_config()
    ds = xa.load_dataset(cfg, year=2025)
    pci = xa.select_analysis(ds, cfg, "pci")
    xa.plot_representative_doses(pci, cfg.analysis("pci"))
    stats = xa.summary_by_procedure(pci)
    xa.export_summary({"PCI 2025": stats}, cfg.reports_dir / "pci_2025.xlsx")
"""

from .cleaning import clean_all
from .columns import DT, IDS7, MAPPED_PROCEDURE, UNMAPPED
from .config import AnalysisConfig, Config, ProcedureConfig, load_config
from .drl import compare_with_drl
from .io import load_dosetrack, load_ids7, read_excel_files
from .logging_utils import setup_logging
from .mapping import MAPPING_REGISTRY, get_mapping, map_procedures
from .merging import merge_ids7_dt
from .pipeline import (
    Dataset,
    filter_exposures_for_procedure,
    load_dataset,
    load_exposure_data,
    plot_representative_doses,
    select_analysis,
)
from .plotting import (
    plot_air_kerma_angle_heatmap,
    plot_representative_dose,
    plot_representative_dose_by_procedure,
)
from .quality import QualityReport
from .reporting import (
    export_examination_codes,
    export_summary,
    print_summary,
    summary_by_procedure,
)
from .trends import plot_trend, plot_trend_per_room, trend_table

__all__ = [
    "DT",
    "IDS7",
    "MAPPED_PROCEDURE",
    "MAPPING_REGISTRY",
    "UNMAPPED",
    "AnalysisConfig",
    "Config",
    "Dataset",
    "ProcedureConfig",
    "QualityReport",
    "clean_all",
    "compare_with_drl",
    "export_examination_codes",
    "export_summary",
    "filter_exposures_for_procedure",
    "get_mapping",
    "load_config",
    "load_dataset",
    "load_dosetrack",
    "load_exposure_data",
    "load_ids7",
    "map_procedures",
    "merge_ids7_dt",
    "plot_air_kerma_angle_heatmap",
    "plot_representative_dose",
    "plot_representative_dose_by_procedure",
    "plot_representative_doses",
    "plot_trend",
    "plot_trend_per_room",
    "print_summary",
    "read_excel_files",
    "select_analysis",
    "setup_logging",
    "summary_by_procedure",
    "trend_table",
]
