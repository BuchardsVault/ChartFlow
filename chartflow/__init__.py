from pathlib import Path
from textx import language, metamodel_from_file

_GRAMMAR = Path(__file__).parent / "grammar" / "chartFlow.tx"

@language("chartflow", "*.cf")
def chartflow_metamodel(**kwargs):
    """
    ChartFlow DSL — build finance charts & calculations.
    """
    return metamodel_from_file(_GRAMMAR, **kwargs)