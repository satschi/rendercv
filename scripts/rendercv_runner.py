#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
import urllib.request
from rendercv.cli.render_command.progress_panel import ProgressPanel
from rendercv.cli.render_command.run_rendercv import run_rendercv
from rendercv.renderer import pdf_png
from rendercv.renderer.path_resolver import resolve_rendercv_file_path
from rendercv.schema.rendercv_model_builder import build_rendercv_dictionary_and_model

FONT_AWESOME_VERSION = "0.6.0"
FONT_AWESOME_CHECKSUMS = {
    "typst.toml": "59dd687a1f75ce0fd69cb0f2d6c2e701fdbeb971e04f6dfd0314e29177b5e502",
    "lib.typ": "411354321c70c4c8630954745420e8ee12603e24c8519bf54d89cd5c9b0d2877",
    "lib-impl.typ": "d9d19a96f1c57fac4070c5caec9d14b6ece872f711874f803c2bb38085b2fd3a",
    "lib-gen-map.typ": "f088eb6ae7b072ad567a8238373eece12da9163bebdcb10b226a3aa4c728b75a",
    "lib-gen-func.typ": "fafbe72def8d291bd79f6a48ebde87eb2197ba7c54d10dfca78cbaf8bf4e351d",
}


def ensure_fontawesome_package(package_root: pathlib.Path) -> None:
    """Download Font Awesome Typst package files into the local cache if missing."""
    destination = package_root / "preview" / "fontawesome" / FONT_AWESOME_VERSION
    destination.mkdir(parents=True, exist_ok=True)
    base_url = (
        "https://raw.githubusercontent.com/typst/packages/main/packages/preview/"
        f"fontawesome/{FONT_AWESOME_VERSION}"
    )
    for filename, expected_hash in FONT_AWESOME_CHECKSUMS.items():
        target_path = destination / filename
        if target_path.exists():
            digest = hashlib.sha256(target_path.read_bytes()).hexdigest()
            if digest == expected_hash:
                continue
        with urllib.request.urlopen(f"{base_url}/{filename}") as response:
            payload = response.read()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != expected_hash:
            raise RuntimeError(
                f"Checksum mismatch for {filename}: expected {expected_hash}, got {digest}"
            )
        target_path.write_bytes(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render CV.yaml to PDF.")
    parser.add_argument(
        "input_file",
        nargs="?",
        default="CV.yaml",
        help="Path to the RenderCV YAML file.",
    )
    parser.add_argument(
        "--output-folder",
        "-o",
        default="rendercv_output",
        help="Output folder for generated files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root_dir = pathlib.Path(__file__).resolve().parents[1]
    input_path = pathlib.Path(args.input_file)
    if not input_path.is_absolute():
        input_path = root_dir / input_path
    input_path = input_path.resolve()
    output_folder = pathlib.Path(args.output_folder)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    package_root = pdf_png.get_package_path()
    ensure_fontawesome_package(package_root)

    main_yaml = input_path.read_text(encoding="utf-8")
    _, rendercv_model = build_rendercv_dictionary_and_model(
        main_yaml,
        input_file_path=input_path,
        output_folder=output_folder,
        dont_generate_markdown=True,
        dont_generate_html=True,
        dont_generate_png=True,
    )
    pdf_path = resolve_rendercv_file_path(
        rendercv_model,
        rendercv_model.settings.render_command.pdf_path,
    )

    with ProgressPanel(quiet=False) as progress:
        run_rendercv(
            input_path,
            progress,
            output_folder=output_folder,
            dont_generate_markdown=True,
            dont_generate_html=True,
            dont_generate_png=True,
        )

    if not pdf_path.exists():
        raise RuntimeError("RenderCV did not produce a PDF output.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
