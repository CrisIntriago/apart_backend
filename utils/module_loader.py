import importlib
import sys
from pathlib import Path


def import_strategies(package: str, base_path: Path):
    """
    Importa todos los módulos Python de una subcarpeta dentro de `strategies`.

    Args:
        package (str): nombre del subpaquete, como 'payload' o 'validation'
        base_path (Path): la ruta base al directorio del proyecto (usualmente Path(__file__).parent.parent)
    """  # noqa: E501
    strategy_dir = base_path / "strategies" / package

    for file in strategy_dir.glob("*.py"):
        if file.name == "__init__.py" or file.name.startswith("_"):
            continue

        module_path = f"activities.strategies.{package}.{file.stem}"
        if module_path not in sys.modules:
            importlib.import_module(module_path)
