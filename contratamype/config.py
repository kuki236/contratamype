"""Configuration and canonical catalogs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

CATEGORY_VALUES = {"goods", "services", "works"}

DEPARTMENT_CODES = {
    "AMAZONAS": "01",
    "ANCASH": "02",
    "APURIMAC": "03",
    "AREQUIPA": "04",
    "AYACUCHO": "05",
    "CAJAMARCA": "06",
    "CALLAO": "07",
    "CUSCO": "08",
    "HUANCAVELICA": "09",
    "HUANUCO": "10",
    "ICA": "11",
    "JUNIN": "12",
    "LA LIBERTAD": "13",
    "LAMBAYEQUE": "14",
    "LIMA": "15",
    "LORETO": "16",
    "MADRE DE DIOS": "17",
    "MOQUEGUA": "18",
    "PASCO": "19",
    "PIURA": "20",
    "PUNO": "21",
    "SAN MARTIN": "22",
    "TACNA": "23",
    "TUMBES": "24",
    "UCAYALI": "25",
    "PROVINCIA CONSTITUCIONAL DEL CALLAO": "07",
}


@dataclass(slots=True)
class Settings:
    artifacts_dir: Path = Path("artifacts/e2e")
    db_path: Path = Path("data/processed/contratamype.duckdb")
    year: int = 2025
    cohort_year: int = 2025
    mype_threshold: Decimal = Decimal("200000")
    target_categories: tuple[str, ...] = ("goods", "services")
    target_departments: tuple[str, ...] = ()
    batch_size: int = 5_000

    def __post_init__(self) -> None:
        self.artifacts_dir = Path(self.artifacts_dir)
        self.db_path = Path(self.db_path)
        self.mype_threshold = Decimal(str(self.mype_threshold))
        self.target_categories = tuple(self.target_categories)
        self.target_departments = tuple(self.target_departments)
