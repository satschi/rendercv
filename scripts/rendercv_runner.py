#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import pathlib
import shutil
import sys
import urllib.request

import rendercv
from rendercv.cli.render_command.progress_panel import ProgressPanel
from rendercv.cli.render_command.run_rendercv import run_rendercv
from rendercv.renderer import pdf_png
from rendercv.renderer.path_resolver import resolve_rendercv_file_path
from rendercv.schema.rendercv_model_builder import build_rendercv_dictionary_and_model

FONT_AWESOME_VERSION = "0.6.0"
FONT_AWESOME_FILES = (
    "typst.toml",
    "lib.typ",
    "lib-impl.typ",
    "lib-gen-map.typ",
    "lib-gen-func.typ",
)


def read_typst_package_version(typst_toml_path: pathlib.Path) -> str:
    for line in typst_toml_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("version"):
            return stripped.split("=", 1)[1].strip().strip('"')
    raise RuntimeError(f"Unable to find version in {typst_toml_path}")


def ensure_rendercv_package(package_root: pathlib.Path) -> None:
    source = pathlib.Path(rendercv.__file__).parent / "renderer" / "rendercv_typst"
    version = read_typst_package_version(source / "typst.toml")
    destination = package_root / "preview" / "rendercv" / version
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)


def ensure_fontawesome_package(package_root: pathlib.Path) -> None:
    destination = package_root / "preview" / "fontawesome" / FONT_AWESOME_VERSION
    if (destination / "typst.toml").exists():
        return
    destination.mkdir(parents=True, exist_ok=True)
    base_url = (
        "https://raw.githubusercontent.com/typst/packages/main/packages/preview/"
        f"fontawesome/{FONT_AWESOME_VERSION}"
    )
    for filename in FONT_AWESOME_FILES:
        urllib.request.urlretrieve(f"{base_url}/{filename}", destination / filename)


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

    package_root = root_dir / ".typst-packages"
    ensure_rendercv_package(package_root)
    ensure_fontawesome_package(package_root)

    def package_path_override() -> pathlib.Path:
        return package_root

    pdf_png.get_package_path = functools.lru_cache(maxsize=1)(package_path_override)

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
