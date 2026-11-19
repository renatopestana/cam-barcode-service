"""Regras de validação EAN-13 e fatiamento de etiquetas de balança."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Optional


def ean13_check_digit(d12: str) -> str:
    """Calcula o dígito verificador EAN-13 a partir dos 12 primeiros dígitos."""
    if len(d12) != 12 or not d12.isdigit():
        raise ValueError(f"Esperados 12 dígitos numéricos, recebido: {d12!r}")
    soma = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d12))
    return str((10 - soma % 10) % 10)


def is_valid_ean13(code: str) -> bool:
    """Verifica se uma string é um código EAN-13 válido."""
    return len(code) == 13 and code.isdigit() and code[12] == ean13_check_digit(code[:12])


@dataclass(frozen=True)
class Layout:
    """Descreve como os 12 dígitos de dados de uma etiqueta de balança estão divididos."""

    name: str
    prefix_len: int  # ex.: 1 -> "2"
    plu_len: int  # tamanho do código do produto (PLU)
    const_len: int  # dígitos fixos entre o PLU e o valor (ex.: "0")
    value_len: int  # tamanho do campo de valor/peso
    kind: str  # "price" (centavos) ou "weight" (gramas)

    @property
    def data_len(self) -> int:
        return self.prefix_len + self.plu_len + self.const_len + self.value_len

    def validate(self) -> None:
        if self.data_len != 12:
            raise ValueError(
                f"Layout '{self.name}': prefixo+PLU+const+valor = {self.data_len}, "
                "mas deveria somar 12 (o 13º dígito é o verificador)."
            )
        if self.kind not in ("price", "weight"):
            raise ValueError("kind deve ser 'price' ou 'weight'.")


PRESETS: dict[str, Layout] = {
    # 2 00031 0 00406 D  -> 5 dígitos de PLU + 1 constante + 5 dígitos de preço
    "plataforma5": Layout("plataforma5", 1, 5, 1, 5, "price"),
    # 2 000031 00406 D   -> 6 dígitos de PLU + 5 dígitos de preço
    "plataforma6": Layout("plataforma6", 1, 6, 0, 5, "price"),
    "peso5": Layout("peso5", 1, 5, 1, 5, "weight"),
    "peso6": Layout("peso6", 1, 6, 0, 5, "weight"),
    # 2 0031 0 000406 D  -> 4 dígitos de PLU + 1 constante + 6 dígitos de preço
    "plu4": Layout("plu4", 1, 4, 1, 6, "price"),
}


@dataclass(frozen=True)
class Product:
    code: int
    name: str
    price_kg: Decimal


@dataclass
class Scan:
    raw: str
    layout: Layout
    check_ok: bool
    is_scale_label: bool  # começa com "2" (faixa de uso interno / preço variável)
    prefix: str
    plu_str: str
    const: str
    value_str: str
    check_digit: str
    plu: int
    price: Optional[Decimal] = None  # R$
    weight: Optional[Decimal] = None  # kg
    product: Optional[Product] = None

    def to_dict(self) -> dict[str, Any]:
        """Serializa a leitura para dicionário pronto para JSON/Webhook."""
        return {
            "raw": self.raw,
            "layout": self.layout.name,
            "check_ok": self.check_ok,
            "is_scale_label": self.is_scale_label,
            "prefix": self.prefix,
            "plu": self.plu,
            "plu_str": self.plu_str,
            "const": self.const,
            "value_str": self.value_str,
            "check_digit": self.check_digit,
            "price": float(self.price) if self.price is not None else None,
            "weight": float(self.weight) if self.weight is not None else None,
            "product": (
                {
                    "code": self.product.code,
                    "name": self.product.name,
                    "price_kg": float(self.product.price_kg),
                }
                if self.product
                else None
            ),
        }


def _q(value: Decimal, places: str) -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def parse_label(
    code: str,
    layout: Layout,
    products: Optional[dict[int, Product]] = None,
) -> Scan:
    """Fatia um EAN-13 de balança conforme o layout informado.

    Levanta ValueError se o código não tiver 13 dígitos numéricos ou o layout for inválido.
    """
    layout.validate()
    code = code.strip()
    if len(code) != 13 or not code.isdigit():
        raise ValueError(f"Código deve ter 13 dígitos numéricos: {code!r}")

    i = 0
    prefix = code[i : i + layout.prefix_len]
    i += layout.prefix_len
    plu_str = code[i : i + layout.plu_len]
    i += layout.plu_len
    const = code[i : i + layout.const_len]
    i += layout.const_len
    value_str = code[i : i + layout.value_len]
    i += layout.value_len
    dv = code[i]

    scan = Scan(
        raw=code,
        layout=layout,
        check_ok=is_valid_ean13(code),
        is_scale_label=code.startswith("2"),
        prefix=prefix,
        plu_str=plu_str,
        const=const,
        value_str=value_str,
        check_digit=dv,
        plu=int(plu_str),
    )

    valor = Decimal(int(value_str))
    if layout.kind == "price":
        scan.price = _q(valor / 100, "0.01")
    else:
        scan.weight = _q(valor / 1000, "0.001")

    if products and scan.plu in products:
        prod = products[scan.plu]
        scan.product = prod
        if prod.price_kg > 0:
            if scan.price is not None and scan.weight is None:
                scan.weight = _q(scan.price / prod.price_kg, "0.001")
            elif scan.weight is not None and scan.price is None:
                scan.price = _q(scan.weight * prod.price_kg, "0.01")
    return scan


def brl(value: Optional[Decimal]) -> str:
    return "-" if value is None else f"R$ {value:.2f}".replace(".", ",")


def kg(value: Optional[Decimal]) -> str:
    return "-" if value is None else f"{value:.3f} kg".replace(".", ",")


def describe(scan: Scan) -> list[str]:
    """Formata linhas legíveis para console e overlay (ASCII compatível com OpenCV)."""
    lay = scan.layout
    nome = scan.product.name if scan.product else "(produto nao cadastrado no CSV)"
    return [
        f"{scan.raw}  [{lay.name}]  DV {'OK' if scan.check_ok else 'INVALIDO'}",
        f"Prefixo {scan.prefix} | PLU {scan.plu_str} | Const {scan.const or '-'} | "
        f"{'Valor' if lay.kind == 'price' else 'Peso'} {scan.value_str} | DV {scan.check_digit}",
        f"Produto {scan.plu}: {nome}",
        f"Preco {brl(scan.price)}   Peso {kg(scan.weight)}"
        + (f"   (R$/kg {scan.product.price_kg:.2f})".replace(".", ",") if scan.product else ""),
    ]


def load_products(path: Path) -> dict[int, Product]:
    """Carrega catálogo opcional de produtos (CSV com colunas: codigo, nome, preco_kg)."""
    products: dict[int, Product] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        head = f.readline()
        f.seek(0)
        delim = ";" if head.count(";") > head.count(",") else ","
        for row in csv.DictReader(f, delimiter=delim):
            clean = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            code = int(clean["codigo"])
            price = Decimal(clean.get("preco_kg", "0").replace(",", ".") or "0")
            products[code] = Product(code, clean.get("nome", ""), price)
    return products
