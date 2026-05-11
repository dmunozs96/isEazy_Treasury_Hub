from pathlib import Path

from .parsers import ALL_PARSERS, BankParser


def detect_parser(filename: str) -> BankParser:
    """
    Return the first parser that claims it can handle the given filename.
    Raises ValueError if no parser matches.
    """
    name = Path(filename).name
    for parser in ALL_PARSERS:
        if parser.can_parse(name):
            return parser
    raise ValueError(
        f"No parser found for file '{name}'. "
        f"Expected filename prefix: Abanca_, BBVA_, BancaMarch_, Bankinter_, "
        f"Caixa_, Cajamar_, DEUSTCHE_, EUROCAJA_, Ibercaja_, Ruralvia_, "
        f"Sabadell_, Santander_."
    )
