"""Loading of the analysis configuration from ``config.toml``.

The configuration file collects everything that used to be hardcoded in the
notebooks: data folder locations per machine, room-name standardization,
and per-analysis settings (rooms, mapping dictionary, procedures to plot,
optional diagnostic reference levels).
"""

import os
import socket
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILENAME = "config.toml"

# Environment override for the data root. Set this to point an analysis run at a
# different folder than the one configured for the machine in config.toml.
DATA_ROOT_ENV_VAR = "XA_DOSE_DATA_ROOT"


@dataclass(frozen=True)
class ProcedureConfig:
    """Settings for one procedure within an analysis."""

    name: str
    y_max: float | None = None  # y-axis limit for boxplots (Gy*cm2)
    drl_dap: float | None = None  # diagnostic reference level, DAP (Gy*cm2)
    drl_cak: float | None = None  # diagnostic reference level, CAK (mGy)


@dataclass(frozen=True)
class AnalysisConfig:
    """Settings for one analysis (one [analyses.<name>] block)."""

    name: str
    rooms: list[str] = field(default_factory=list)  # empty = no room filter
    mapping: str | None = None  # key in mapping.MAPPING_REGISTRY
    max_age: float | None = None  # keep only patients younger than this
    procedures: list[ProcedureConfig] = field(default_factory=list)

    def procedure(self, name: str) -> ProcedureConfig:
        """Look up a procedure by name; raises KeyError if not configured."""
        for proc in self.procedures:
            if proc.name == name:
                return proc
        raise KeyError(f"Procedure '{name}' is not configured for analysis '{self.name}'")

    @property
    def procedure_names(self) -> list[str]:
        return [proc.name for proc in self.procedures]


@dataclass(frozen=True)
class Config:
    """The full configuration loaded from config.toml."""

    config_dir: Path  # folder containing config.toml; output paths are relative to it
    data_roots: dict[str, str]  # hostname -> data root folder ("default" = fallback)
    ids7_subfolder: str
    dosetrack_subfolder: str
    exposure_subfolder: str
    figures_folder: str
    reports_folder: str
    room_aliases: dict[str, list[str]]  # standard name -> list of variants
    analyses: dict[str, AnalysisConfig]

    @property
    def data_root(self) -> Path:
        """The data root folder for the current machine (by hostname).

        ``XA_DOSE_DATA_ROOT`` overrides the configured roots when set.
        """
        override = os.environ.get(DATA_ROOT_ENV_VAR)
        if override:
            return Path(override)
        hostname = socket.gethostname()
        try:
            root = self.data_roots.get(hostname) or self.data_roots["default"]
        except KeyError:
            raise KeyError(
                f"No data root configured for host '{hostname}' and no 'default' entry "
                f"in [paths.data_root] in {self.config_dir / CONFIG_FILENAME}"
            ) from None
        return Path(root)

    @property
    def figures_dir(self) -> Path:
        return self.config_dir / self.figures_folder

    @property
    def reports_dir(self) -> Path:
        return self.config_dir / self.reports_folder

    def ids7_folder(self, year: str | int | None = None) -> Path:
        """Folder with IDS7 Excel exports, optionally for a specific year."""
        return self._data_folder(self.ids7_subfolder, year)

    def dosetrack_folder(self, year: str | int | None = None) -> Path:
        """Folder with procedure-level DoseTrack exports, optionally per year."""
        return self._data_folder(self.dosetrack_subfolder, year)

    def exposure_folder(self, year: str | int | None = None) -> Path:
        """Folder with exposure-level DoseTrack exports, optionally per year."""
        return self._data_folder(self.exposure_subfolder, year)

    def _data_folder(self, subfolder: str, year: str | int | None) -> Path:
        folder = self.data_root / subfolder
        if year is not None:
            folder = folder / str(year)
        return folder

    def analysis(self, name: str) -> AnalysisConfig:
        """Look up an analysis by name with a helpful error message."""
        try:
            return self.analyses[name]
        except KeyError:
            available = ", ".join(sorted(self.analyses))
            raise KeyError(f"Unknown analysis '{name}'. Configured analyses: {available}") from None


def find_config_file(start: Path | None = None) -> Path:
    """Search for config.toml in `start` (default cwd) and its parent folders."""
    folder = (start or Path.cwd()).resolve()
    for candidate_dir in [folder, *folder.parents]:
        candidate = candidate_dir / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"Could not find {CONFIG_FILENAME} in {folder} or any parent folder. "
        "Run from within the project, or pass the path to load_config()."
    )


def load_config(path: str | Path | None = None) -> Config:
    """Load the configuration.

    Parameters
    ----------
    path:
        Path to a config.toml file. If None, the file is searched for in the
        current working directory and its parents (so notebooks in
        ``notebooks/`` find the repository-root config automatically).
    """
    config_path = Path(path) if path is not None else find_config_file()
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    paths = raw.get("paths", {})
    data = raw.get("data", {})

    analyses = {name: _parse_analysis(name, block) for name, block in raw.get("analyses", {}).items()}

    return Config(
        config_dir=config_path.resolve().parent,
        data_roots=paths.get("data_root", {}),
        ids7_subfolder=data.get("ids7_subfolder", "IDS7"),
        dosetrack_subfolder=data.get("dosetrack_subfolder", "DoseTrack - Serienivå"),
        exposure_subfolder=data.get("exposure_subfolder", "DoseTrack - Eksponeringsnivå"),
        figures_folder=paths.get("figures", "Figures"),
        reports_folder=paths.get("reports", "Reports"),
        room_aliases=raw.get("room_aliases", {}),
        analyses=analyses,
    )


def _parse_analysis(name: str, block: dict) -> AnalysisConfig:
    procedures = [
        ProcedureConfig(
            name=proc["name"],
            y_max=proc.get("y_max"),
            drl_dap=proc.get("drl_dap"),
            drl_cak=proc.get("drl_cak"),
        )
        for proc in block.get("procedures", [])
    ]
    return AnalysisConfig(
        name=name,
        rooms=block.get("rooms", []),
        mapping=block.get("mapping"),
        max_age=block.get("max_age"),
        procedures=procedures,
    )
