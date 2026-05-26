"""CLI entry point for the Gradio app."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reinforced-slicer-gui",
        description="Launch the Reinforced-Slicer Gradio app.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7860, help="Port to listen on (default: 7860)")
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public share link via Gradio's tunnelling service.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the system browser on launch.",
    )
    args = parser.parse_args(argv)

    import gradio as gr

    from reinforced_slicer.gui.app import build_app

    demo = build_app()
    demo.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        inbrowser=not args.no_browser,
        show_error=True,
        theme=gr.themes.Soft(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
