"""Gradio-based GUI for the slicer.

Optional sub-package — install with ``pip install -e .[gui]``. The
top-level slicer library has no Gradio dependency, so importing the
core ``reinforced_slicer`` modules works fine without Gradio installed.
The GUI lives in its own sub-package so it can carry its own deps and
its own unit tests without polluting the headless code path.
"""
