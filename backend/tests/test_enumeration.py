import inspect
from enum import Enum

import pytest

from common import enumeration

ENUMS = [
    obj for _, obj in inspect.getmembers(enumeration, inspect.isclass)
    if issubclass(obj, Enum) and obj.__module__ == enumeration.__name__
]


@pytest.mark.parametrize("enum_cls", ENUMS, ids=lambda e: e.__name__)
def test_valeurs_canoniques_egales_aux_noms(enum_cls):
    """Les valeurs stockées en base sont les noms en MAJUSCULES (spéc. §19.3)."""
    for member in enum_cls:
        assert member.value == member.name
        assert member.value.isupper()


def test_enums_metier_clefs():
    assert {s.value for s in enumeration.DocStage} == {
        "QUOTE", "RFQ", "ORDER", "DELIVERY", "RECEIPT", "INVOICE", "BILL", "CREDIT_NOTE"}
    assert "BATCH_EXPIRY" not in {s.value for s in enumeration.StockTracking}
