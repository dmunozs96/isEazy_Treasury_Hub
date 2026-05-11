from .abanca import AbancaParser
from .banca_march import BancaMarchParser
from .bankinter import BankinterParser
from .base import BankParser, ParsedRow
from .bbva import BBVAParser
from .caixabank import CaixaBankParser
from .cajamar import CajamarParser
from .deutsche_bank import DeutscheBankParser
from .eurocaja_rural import EurocajaRuralParser
from .ibercaja import IbercajaParser
from .ruralvia import RuralviaParser
from .sabadell import SabadellParser
from .santander import SantanderParser

ALL_PARSERS: list[BankParser] = [
    AbancaParser(),
    BBVAParser(),
    BancaMarchParser(),
    BankinterParser(),
    CaixaBankParser(),
    CajamarParser(),
    DeutscheBankParser(),
    EurocajaRuralParser(),
    IbercajaParser(),
    RuralviaParser(),
    SabadellParser(),
    SantanderParser(),
]

__all__ = [
    "BankParser",
    "ParsedRow",
    "AbancaParser",
    "BBVAParser",
    "BancaMarchParser",
    "BankinterParser",
    "CaixaBankParser",
    "CajamarParser",
    "DeutscheBankParser",
    "EurocajaRuralParser",
    "IbercajaParser",
    "RuralviaParser",
    "SabadellParser",
    "SantanderParser",
    "ALL_PARSERS",
]
