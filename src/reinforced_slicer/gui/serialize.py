"""Serialize slicer outputs into UI-consumable artefacts.

Keeps the GUI layer agnostic of slicer internals: the Gradio code
receives plotly figures, file paths to OBJ meshes, and dicts of stats,
and never has to touch ``SlicedPart`` / ``IsoSurface`` / ``CutterPose``
directly. That keeps the UI swappable (Streamlit, Tauri, …) and the
serialization separately testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from reinforced_slicer.kinematics import CutterPose, JointState
from reinforced_slicer.mesh.isosurface import IsoSurface
from reinforced_slicer.slicing.curved_5axis import CurvedSlicePipelineResult
from reinforced_slicer.slicing.planar import SlicedPart

OrientedLayer = list[list[CutterPose]]


# --- Mesh stats ----------------------------------------------------------


def mesh_stats(mesh: trimesh.Trimesh) -> dict[str, Any]:
    """Geometry and quality stats for a triangle mesh.

    Slicer-relevant quality flags:
    - ``watertight``: every edge is shared by exactly two faces. Required
      for reliable planar slicing.
    - ``n_open_edges``: edges shared by < 2 faces (holes / boundaries).
    - ``n_non_manifold_edges``: edges shared by > 2 faces (corrupt geometry).
    - ``n_broken_faces``: faces with zero area.
    - ``slicing_ready``: composite — watertight, manifold, no broken faces.
    """
    bounds = mesh.bounds
    extent = bounds[1] - bounds[0]
    n_open_edges = _count_edges_with_multiplicity(mesh, multiplicity=1)
    n_non_manifold_edges = _count_edges_with_multiplicity(mesh, multiplicity=3, at_least=True)
    n_broken = int(len(getattr(mesh, "broken_faces", []) or []))

    watertight = bool(mesh.is_watertight)
    is_winding_consistent = bool(getattr(mesh, "is_winding_consistent", True))
    slicing_ready = (
        watertight and is_winding_consistent and n_broken == 0 and n_non_manifold_edges == 0
    )

    return {
        "n_vertices": int(len(mesh.vertices)),
        "n_faces": int(len(mesh.faces)),
        "extent_mm": [round(float(x), 3) for x in extent],
        "bbox_min_mm": [round(float(x), 3) for x in bounds[0]],
        "bbox_max_mm": [round(float(x), 3) for x in bounds[1]],
        "volume_mm3": round(float(mesh.volume), 3) if mesh.is_volume else None,
        "watertight": watertight,
        "winding_consistent": is_winding_consistent,
        "n_open_edges": n_open_edges,
        "n_non_manifold_edges": n_non_manifold_edges,
        "n_broken_faces": n_broken,
        "slicing_ready": slicing_ready,
    }


def _count_edges_with_multiplicity(mesh: trimesh.Trimesh, multiplicity: int, at_least: bool = False) -> int:
    """Count edges shared by exactly (or at least) ``multiplicity`` faces.

    Uses trimesh's edge grouping. ``at_least=True`` includes higher counts —
    use it for non-manifold detection (3+ faces sharing an edge).
    """
    try:
        edges_sorted = mesh.edges_sorted
        # Group identical edge rows.
        from collections import Counter

        counts = Counter(map(tuple, edges_sorted))
        if at_least:
            return sum(1 for v in counts.values() if v >= multiplicity)
        return sum(1 for v in counts.values() if v == multiplicity)
    except Exception:
        return 0


def mesh_quality_warning(stats: dict[str, Any]) -> str | None:
    """Return a markdown warning string if ``stats`` flag mesh issues.

    Returns ``None`` for a clean mesh — callers can hide the warning panel.
    """
    issues: list[str] = []
    if not stats.get("watertight", True):
        issues.append(
            f"**Not watertight** — {stats.get('n_open_edges', 0)} open edges. "
            "Planar slicing may produce gaps; curved-layer pipeline runs on the "
            "AABB so this matters less but the input geometry is still off."
        )
    if not stats.get("winding_consistent", True):
        issues.append(
            "**Winding inconsistent** — face normals point in incompatible "
            "directions. Try `trimesh.repair.fix_normals` on the input."
        )
    if stats.get("n_broken_faces", 0) > 0:
        issues.append(
            f"**{stats['n_broken_faces']} broken (zero-area) faces.** "
            "Run `trimesh.repair.fix_inversion` and `mesh.update_faces(mesh.unique_faces())`."
        )
    if not issues:
        return None
    return "⚠️ Mesh quality warnings:\n\n" + "\n\n".join(f"- {x}" for x in issues)


# --- Planar slice export -------------------------------------------------


def planar_slice_stats(part: SlicedPart) -> dict[str, Any]:
    n_paths = sum(len(layer.paths) for layer in part.layers)
    n_points = sum(sum(len(p) for p in layer.paths) for layer in part.layers)
    z_min = min((layer.z for layer in part.layers), default=0.0)
    z_max = max((layer.z for layer in part.layers), default=0.0)
    return {
        "n_layers": len(part.layers),
        "layer_height_mm": part.config.layer_height,
        "infill_spacing_mm": part.config.infill_spacing,
        "n_paths_total": n_paths,
        "n_path_points": n_points,
        "z_range_mm": [round(z_min, 3), round(z_max, 3)],
    }


def planar_slice_plotly(
    part: SlicedPart,
    max_layers: int | None = 60,
    layer_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Return a plotly Figure showing per-layer paths in 3D.

    ``layer_range`` is an inclusive ``(lo, hi)`` index pair in the original
    layer ordering — pass ``(0, N-1)`` for the full stack, ``(i, i)`` for a
    single layer. ``max_layers`` then downsamples the selection further so
    huge ranges still render quickly.
    """
    import plotly.graph_objects as go

    layers = part.layers
    if layer_range is not None:
        lo, hi = layer_range
        lo = max(0, int(lo))
        hi = min(len(layers) - 1, int(hi))
        layers = layers[lo : hi + 1]
    if max_layers is not None and len(layers) > max_layers:
        idx = np.linspace(0, len(layers) - 1, max_layers).astype(int)
        layers = [layers[i] for i in idx]

    traces: list[go.Scatter3d] = []
    for li, layer in enumerate(layers):
        colour = _layer_colour(li, len(layers))
        for poly in layer.paths:
            traces.append(
                go.Scatter3d(
                    x=poly[:, 0],
                    y=poly[:, 1],
                    z=np.full(len(poly), layer.z),
                    mode="lines",
                    line={"color": colour, "width": 2},
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    fig = go.Figure(data=traces)
    fig.update_layout(
        scene={"aspectmode": "data", "xaxis_title": "X", "yaxis_title": "Y", "zaxis_title": "Z"},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=560,
    )
    return fig


# --- Curved layer export -------------------------------------------------


def curved_layer_stats(result: CurvedSlicePipelineResult) -> dict[str, Any]:
    displ = result.curvi_result.displacement
    return {
        "n_layers": result.n_layers,
        "n_paths_total": result.n_paths,
        "n_path_points": result.n_path_points,
        "z_target_mm": round(result.curvi_result.z_target, 3),
        "osqp_status": result.curvi_result.osqp_status,
        "displacement_range_mm": [round(float(displ.min()), 3), round(float(displ.max()), 3)],
        "field_range": [round(float(result.field.min()), 3), round(float(result.field.max()), 3)],
        "gcode_lines": result.gcode.count("\n"),
    }


def export_iso_surfaces_obj(layers: list[IsoSurface], output_path: Path) -> Path:
    """Combine all iso-surface triangle meshes into one OBJ file for Model3D."""
    meshes: list[trimesh.Trimesh] = []
    for iso in layers:
        if iso.is_empty():
            continue
        meshes.append(
            trimesh.Trimesh(vertices=iso.vertices, faces=iso.triangles, process=False)
        )
    if not meshes:
        # Write an empty OBJ so callers can still hand a path to the UI.
        output_path.write_text("# empty surface\n")
        return output_path
    combined = trimesh.util.concatenate(meshes)
    combined.export(output_path)
    return output_path


def curved_layers_plotly(
    layers: list[IsoSurface],
    oriented_layers: list[OrientedLayer],
    show_normals_every: int = 12,
    layer_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Plotly figure: curved-layer surfaces + tool paths + sample tool axes.

    ``layer_range`` filters the visible layers as in ``planar_slice_plotly``;
    pass ``None`` to show all layers.
    """
    import plotly.graph_objects as go

    traces: list[go.BaseTraceType] = []
    n_layers_total = len(layers)

    if layer_range is not None:
        lo, hi = layer_range
        lo = max(0, int(lo))
        hi = min(n_layers_total - 1, int(hi))
        visible = set(range(lo, hi + 1))
    else:
        visible = set(range(n_layers_total))

    n_layers = n_layers_total  # keep colours stable across filterings

    for li, iso in enumerate(layers):
        if li not in visible:
            continue
        if iso.is_empty():
            continue
        colour = _layer_colour(li, n_layers)
        # Surface mesh
        traces.append(
            go.Mesh3d(
                x=iso.vertices[:, 0],
                y=iso.vertices[:, 1],
                z=iso.vertices[:, 2],
                i=iso.triangles[:, 0],
                j=iso.triangles[:, 1],
                k=iso.triangles[:, 2],
                color=colour,
                opacity=0.35,
                showscale=False,
                hoverinfo="skip",
                name=f"layer {li}",
            )
        )

    for li, paths in enumerate(oriented_layers):
        if li not in visible:
            continue
        colour = _layer_colour(li, max(n_layers, 1))
        for path in paths:
            if not path:
                continue
            xs = [p.position[0] for p in path]
            ys = [p.position[1] for p in path]
            zs = [p.position[2] for p in path]
            traces.append(
                go.Scatter3d(
                    x=xs, y=ys, z=zs,
                    mode="lines",
                    line={"color": colour, "width": 4},
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            # Sample tool axes as line segments.
            if show_normals_every > 0:
                samples = list(range(0, len(path), show_normals_every))
                if samples:
                    norm_len = 0.05 * _layer_scale(layers)
                    arrow_x: list[float] = []
                    arrow_y: list[float] = []
                    arrow_z: list[float] = []
                    for idx in samples:
                        pose = path[idx]
                        tip = pose.position + norm_len * pose.tool_axis
                        arrow_x.extend([pose.position[0], tip[0], None])
                        arrow_y.extend([pose.position[1], tip[1], None])
                        arrow_z.extend([pose.position[2], tip[2], None])
                    traces.append(
                        go.Scatter3d(
                            x=arrow_x, y=arrow_y, z=arrow_z,
                            mode="lines",
                            line={"color": "black", "width": 2},
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )

    fig = go.Figure(data=traces)
    fig.update_layout(
        scene={"aspectmode": "data", "xaxis_title": "X", "yaxis_title": "Y", "zaxis_title": "Z"},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=620,
    )
    return fig


# --- Kinematics export ---------------------------------------------------


def joint_trajectory_plotly(
    poses: list[CutterPose],
    joints: list[JointState],
    singularity: list[float],
) -> dict[str, Any]:
    """Two-row plotly figure: rotary trajectory + singularity distance."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    n = len(poses)
    sample_idx = list(range(n))
    a_deg = [float(np.degrees(j.rotary[0])) for j in joints]
    c_deg = [float(np.degrees(j.rotary[1])) for j in joints]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=("Rotary axes (A, C) along path", "Distance from singularity (sin A)"),
        vertical_spacing=0.12,
        row_heights=[0.55, 0.45],
    )
    fig.add_trace(
        go.Scatter(x=sample_idx, y=a_deg, mode="lines", name="A (deg)", line={"color": "tomato"}),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=sample_idx, y=c_deg, mode="lines", name="C (deg)", line={"color": "steelblue"}),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=sample_idx, y=singularity, mode="lines", name="sin A", line={"color": "seagreen"}),
        row=2, col=1,
    )
    fig.update_xaxes(title_text="Path sample index", row=2, col=1)
    fig.update_yaxes(title_text="Joint angle (deg)", row=1, col=1)
    fig.update_yaxes(title_text="Singularity distance", row=2, col=1)
    fig.update_layout(height=540, margin={"l": 50, "r": 10, "t": 40, "b": 40})
    return fig


# --- helpers --------------------------------------------------------------


def _layer_colour(i: int, total: int) -> str:
    """Map layer index to an RGB string spanning a turbo-like palette."""
    if total <= 1:
        return "rgb(80, 140, 220)"
    t = i / max(total - 1, 1)
    r = int(255 * min(1.0, max(0.0, 1.5 - abs(4 * t - 3))))
    g = int(255 * min(1.0, max(0.0, 1.5 - abs(4 * t - 2))))
    b = int(255 * min(1.0, max(0.0, 1.5 - abs(4 * t - 1))))
    return f"rgb({r}, {g}, {b})"


def _layer_scale(layers: list[IsoSurface]) -> float:
    """Characteristic length for sizing tool-axis arrows."""
    for iso in layers:
        if not iso.is_empty():
            extent = iso.vertices.max(axis=0) - iso.vertices.min(axis=0)
            return float(max(extent))
    return 1.0


@dataclass(frozen=True)
class PlanarSliceArtifacts:
    gcode_path: Path
    plotly_fig: Any
    stats: dict[str, Any]


@dataclass(frozen=True)
class CurvedSliceArtifacts:
    gcode_path: Path
    layers_obj_path: Path
    plotly_fig: Any
    stats: dict[str, Any]


def side_by_side_plotly(
    part: SlicedPart,
    iso_layers: list[IsoSurface],
    oriented_layers: list[OrientedLayer],
    show_normals_every: int = 16,
) -> dict[str, Any]:
    """Side-by-side comparison: planar paths (left) vs curved layers (right)."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "scene"}, {"type": "scene"}]],
        subplot_titles=("3-axis planar", "5-axis curved layers"),
        horizontal_spacing=0.02,
    )

    n_planar = len(part.layers)
    for li, layer in enumerate(part.layers):
        colour = _layer_colour(li, n_planar)
        for poly in layer.paths:
            fig.add_trace(
                go.Scatter3d(
                    x=poly[:, 0], y=poly[:, 1],
                    z=np.full(len(poly), layer.z),
                    mode="lines",
                    line={"color": colour, "width": 2},
                    showlegend=False, hoverinfo="skip",
                ),
                row=1, col=1,
            )

    n_curved = len(iso_layers)
    for li, iso in enumerate(iso_layers):
        if iso.is_empty():
            continue
        colour = _layer_colour(li, n_curved)
        fig.add_trace(
            go.Mesh3d(
                x=iso.vertices[:, 0], y=iso.vertices[:, 1], z=iso.vertices[:, 2],
                i=iso.triangles[:, 0], j=iso.triangles[:, 1], k=iso.triangles[:, 2],
                color=colour, opacity=0.4,
                showscale=False, hoverinfo="skip",
            ),
            row=1, col=2,
        )
    for li, paths in enumerate(oriented_layers):
        colour = _layer_colour(li, max(n_curved, 1))
        for path in paths:
            if not path:
                continue
            fig.add_trace(
                go.Scatter3d(
                    x=[p.position[0] for p in path],
                    y=[p.position[1] for p in path],
                    z=[p.position[2] for p in path],
                    mode="lines",
                    line={"color": colour, "width": 3},
                    showlegend=False, hoverinfo="skip",
                ),
                row=1, col=2,
            )
            if show_normals_every > 0:
                norm_len = 0.04 * _layer_scale(iso_layers)
                arrow_x: list[float] = []
                arrow_y: list[float] = []
                arrow_z: list[float] = []
                for idx in range(0, len(path), show_normals_every):
                    pose = path[idx]
                    tip = pose.position + norm_len * pose.tool_axis
                    arrow_x.extend([pose.position[0], tip[0], None])
                    arrow_y.extend([pose.position[1], tip[1], None])
                    arrow_z.extend([pose.position[2], tip[2], None])
                if arrow_x:
                    fig.add_trace(
                        go.Scatter3d(
                            x=arrow_x, y=arrow_y, z=arrow_z,
                            mode="lines",
                            line={"color": "black", "width": 2},
                            showlegend=False, hoverinfo="skip",
                        ),
                        row=1, col=2,
                    )

    fig.update_layout(
        scene={"aspectmode": "data"},
        scene2={"aspectmode": "data"},
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        height=640,
    )
    return fig


def comparison_summary_markdown(
    planar_stats: dict[str, Any],
    curved_stats: dict[str, Any],
    planar_print: dict[str, Any],
    curved_print: dict[str, Any],
) -> str:
    """Markdown table comparing the two pipelines."""
    rows = [
        ("Layers", planar_stats.get("n_layers"), curved_stats.get("n_layers")),
        ("Path points", planar_stats.get("n_path_points"), curved_stats.get("n_path_points")),
        ("Print time", planar_print.get("print_time"), curved_print.get("print_time")),
        ("Total time", planar_print.get("total_time"), curved_print.get("total_time")),
        ("Print distance (mm)", planar_print.get("print_distance_mm"), curved_print.get("print_distance_mm")),
        ("Travel distance (mm)", planar_print.get("travel_distance_mm"), curved_print.get("travel_distance_mm")),
        ("Filament (m)", planar_print.get("filament_used_m"), curved_print.get("filament_used_m")),
    ]
    lines = ["| Metric | 3-axis planar | 5-axis curved |", "|---|---|---|"]
    for name, a, b in rows:
        lines.append(f"| **{name}** | {a if a is not None else '—'} | {b if b is not None else '—'} |")
    return "\n".join(lines)
