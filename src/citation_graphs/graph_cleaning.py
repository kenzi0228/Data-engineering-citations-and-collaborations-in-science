from __future__ import annotations

from pathlib import Path

from lxml import etree


def repair_gexf_file(input_path: str | Path, output_path: str | Path) -> None:
    """
    Repair a malformed GEXF/XML file using lxml recovery mode.
    """
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(str(input_path), parser)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wb") as file:
        tree.write(
            file,
            encoding="utf-8",
            pretty_print=True,
            xml_declaration=True,
        )