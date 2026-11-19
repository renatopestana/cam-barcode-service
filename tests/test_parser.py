from decimal import Decimal
import pytest

from cam_barcode_service.parser import (
    PRESETS,
    Layout,
    Product,
    ean13_check_digit,
    is_valid_ean13,
    parse_label,
)


def test_ean13_check_digit_and_validation():
    assert ean13_check_digit("200031000406") == "2"
    assert is_valid_ean13("2000310004062") is True
    assert is_valid_ean13("2200031004066") is False


def test_parse_plataforma5_with_product():
    prods = {31: Product(31, "CONTRA FILE", Decimal("58.00"))}
    scan = parse_label("2000310004062", PRESETS["plataforma5"], prods)

    assert scan.plu == 31
    assert scan.price == Decimal("4.06")
    assert scan.weight == Decimal("0.070")
    assert scan.const == "0"
    assert scan.check_ok is True
    assert scan.is_scale_label is True


def test_parse_plataforma6_and_peso5():
    prods = {31: Product(31, "CONTRA FILE", Decimal("58.00"))}

    s6 = parse_label("2000031004068", PRESETS["plataforma6"], prods)
    assert (s6.plu, s6.price, s6.check_ok) == (31, Decimal("4.06"), True)

    sp = parse_label("2000310000705", PRESETS["peso5"], prods)
    assert sp.weight == Decimal("0.070")
    assert sp.price == Decimal("4.06")


def test_parse_without_products():
    scan = parse_label("2000310005571", PRESETS["plataforma5"])
    assert scan.price == Decimal("5.57")
    assert scan.product is None
    data = scan.to_dict()
    assert data["raw"] == "2000310005571"
    assert data["price"] == 5.57


def test_invalid_layout_raises():
    with pytest.raises(ValueError):
        Layout("invalido", 1, 5, 1, 6, "price").validate()
