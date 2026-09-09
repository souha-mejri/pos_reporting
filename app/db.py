import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "data" / "settings.json"


def _charger_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _sauvegarder_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_parametre(nom: str, defaut=None):
    return _charger_settings().get(nom, defaut)


def set_parametre(nom: str, valeur):
    settings = _charger_settings()
    settings[nom] = valeur
    _sauvegarder_settings(settings)
    return valeur
