import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    token: str
    movimientos_data_source_id: str
    cuentas_data_source_id: str
    presupuesto_data_source_id: str
    dry_run: bool = True

    @classmethod
    def from_env(cls, demo=False):
        if demo:
            return cls("", "", "", "", True)
        values = {
            "token": os.getenv("NOTION_TOKEN", "").strip(),
            "movimientos_data_source_id": os.getenv("NOTION_MOVIMIENTOS_DATA_SOURCE_ID", "").strip(),
            "cuentas_data_source_id": os.getenv("NOTION_CUENTAS_DATA_SOURCE_ID", "").strip(),
            "presupuesto_data_source_id": os.getenv("NOTION_PRESUPUESTO_DATA_SOURCE_ID", "").strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ValueError("Missing configuration: " + ", ".join(missing))
        dry_run = os.getenv("DRY_RUN", "true").lower() not in {"0", "false", "no"}
        return cls(**values, dry_run=dry_run)
