"""Gradio app for the Reinforced-Slicer.

Four tabs, in workflow order:

1. **Load & Preview**: STL upload or a synthetic cube generator; shows
   the 3D model and basic stats. The loaded mesh is shared via Gradio
   state with the slicing tabs.
2. **Planar (3-axis)**: planar slicer with knobs for layer height,
   infill spacing/angle, temperatures. Renders the layer paths in 3D
   and exposes the G-code as a download.
3. **Curved layer (5-axis)**: full M2c pipeline. Configures the
   CurviSlicer QP plus path spacing, routes through the M1.5 5-axis
   G-code emitter. Renders curved layer surfaces with overlaid tool
   paths and sampled tool-axis arrows.
4. **Kinematics inspector**: sweep a tool-axis trajectory through the
   AC-table machine; plot rotary trajectory and singularity distance.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import gradio as gr
import numpy as np
import trimesh

from reinforced_slicer.gui.serialize import (
    CurvedSliceArtifacts,
    PlanarSliceArtifacts,
    curved_layer_stats,
    curved_layers_plotly,
    export_iso_surfaces_obj,
    joint_trajectory_plotly,
    mesh_stats,
    planar_slice_plotly,
    planar_slice_stats,
)
from reinforced_slicer.gui.tetmesh_from_stl import (
    ShoeboxTetMesh,
    shoebox_tet_mesh_from_stl,
    synthetic_tilted_cube,
)
from reinforced_slicer.kinematics import (
    AcTableMachine,
    CutterPose,
    detect_singular_segments,
    smooth_singularities,
)
from reinforced_slicer.mesh.isosurface import extract_curved_layers
from reinforced_slicer.postproc.gcode import GcodeConfig, write_gcode
from reinforced_slicer.postproc.gcode_5axis import write_gcode_5axis
from reinforced_slicer.slicing.curved_5axis import curved_layer_5axis_pipeline
from reinforced_slicer.slicing.curvi_3d import CurviSlicer3DConfig, solve_displacement_3d
from reinforced_slicer.slicing.planar import PlanarSliceConfig, slice_planar

# Module-level scratch directory so Gradio's File component has stable paths.
_WORK_DIR = Path(tempfile.gettempdir()) / "reinforced_slicer_gui"
_WORK_DIR.mkdir(parents=True, exist_ok=True)


# --- Tab 1: load & preview ----------------------------------------------


def _load_uploaded_stl(file_obj: Any) -> tuple[trimesh.Trimesh | None, str, dict[str, Any] | None, str | None]:
    if file_obj is None:
        return None, "Upload a mesh file (STL/OBJ/PLY) to begin.", None, None
    path = Path(file_obj.name if hasattr(file_obj, "name") else file_obj)
    try:
        mesh = trimesh.load(path, force="mesh")
    except Exception as exc:
        return None, f"Could not load {path.name}: {exc}", None, None
    if not isinstance(mesh, trimesh.Trimesh):
        return None, f"{path.name} did not produce a single triangle mesh.", None, None
    stats = mesh_stats(mesh)
    return mesh, f"Loaded **{path.name}** — {stats['n_faces']} faces.", stats, str(path)


def _make_synthetic_cube(extent: float, subdivisions: int, tilt_slope: float):
    shoebox = synthetic_tilted_cube(
        extent=extent, subdivisions=int(subdivisions), tilt_slope_x=tilt_slope
    )
    mesh = _shoebox_to_surface_mesh(shoebox)
    surface_path = _WORK_DIR / "synthetic_cube.stl"
    mesh.export(surface_path)
    stats = mesh_stats(mesh)
    info = f"Synthetic cube: extent={extent} mm, subdivisions={int(subdivisions)}, tilt_slope_x={tilt_slope}"
    return mesh, info, stats, str(surface_path), shoebox


def _shoebox_to_surface_mesh(shoebox: ShoeboxTetMesh) -> trimesh.Trimesh:
    """Build a triangle surface mesh of the shoebox so it can be visualised
    via Model3D and used as an STL placeholder."""
    ox, oy, oz = shoebox.origin_mm
    ex, ey, ez = shoebox.extent_mm
    return trimesh.creation.box(extents=(ex, ey, ez)).apply_translation(
        (ox + ex / 2.0, oy + ey / 2.0, oz + ez / 2.0)
    )


# --- Tab 2: planar slice ------------------------------------------------


def _run_planar_slice(
    mesh: trimesh.Trimesh | None,
    layer_height: float,
    infill_spacing: float,
    infill_angle: float,
    alternate_angle: bool,
    nozzle_temp: int,
    bed_temp: int,
) -> tuple[Any, str, Any, str]:
    if mesh is None:
        return None, "Load a mesh first (Tab 1).", None, ""
    slice_cfg = PlanarSliceConfig(
        layer_height=float(layer_height),
        infill_spacing=float(infill_spacing),
        infill_angle_deg=float(infill_angle),
        alternate_angle=bool(alternate_angle),
    )
    gcode_cfg = GcodeConfig(nozzle_temp_c=int(nozzle_temp), bed_temp_c=int(bed_temp))
    part = slice_planar(mesh, slice_cfg)
    gcode_path = _WORK_DIR / "planar.gcode"
    write_gcode(part, gcode_path, gcode_cfg)
    fig = planar_slice_plotly(part)
    stats = planar_slice_stats(part)
    summary = _format_stats(stats)
    artifacts = PlanarSliceArtifacts(
        gcode_path=gcode_path, plotly_fig=fig, stats=stats
    )
    return fig, summary, str(gcode_path), _gcode_preview(gcode_path)


# --- Tab 3: curved layer ------------------------------------------------


def _run_curved_slice(
    mesh: trimesh.Trimesh | None,
    shoebox: ShoeboxTetMesh | None,
    subdivisions: int,
    layer_height: float,
    path_spacing: float,
    tau_min: float,
    tau_max: float,
    flatness_weight: float,
    smoothness_weight: float,
    z_target_override: float,
    use_z_target_override: bool,
) -> tuple[Any, str, str, str, str]:
    if mesh is None and shoebox is None:
        return None, "Load a mesh first (Tab 1).", "", "", ""

    if shoebox is None:
        shoebox = shoebox_tet_mesh_from_stl(mesh, subdivisions=int(subdivisions))

    cfg = CurviSlicer3DConfig(
        tau_min=float(tau_min),
        tau_max=float(tau_max),
        flatness_weight=float(flatness_weight),
        smoothness_weight=float(smoothness_weight),
        z_target=float(z_target_override) if use_z_target_override else None,
    )
    machine = AcTableMachine()
    result = curved_layer_5axis_pipeline(
        shoebox.mesh,
        shoebox.top_indices,
        shoebox.bottom_indices,
        machine,
        layer_height=float(layer_height),
        path_spacing=float(path_spacing),
        curvi_config=cfg,
    )

    # Re-derive iso-surfaces + oriented layers for visualisation (cheap).
    field = result.field
    iso_layers = extract_curved_layers(shoebox.mesh, field, layer_height=float(layer_height))
    oriented_layers = _replan_paths_for_viz(iso_layers, float(path_spacing))

    obj_path = _WORK_DIR / "curved_layers.obj"
    export_iso_surfaces_obj(iso_layers, obj_path)

    gcode_path = _WORK_DIR / "curved_5axis.gcode"
    gcode_path.write_text(result.gcode)

    fig = curved_layers_plotly(iso_layers, oriented_layers, show_normals_every=12)
    stats = curved_layer_stats(result)
    summary = (
        _format_stats(stats)
        + f"\n\n*{shoebox.note}*"
    )
    return fig, summary, str(obj_path), str(gcode_path), _gcode_preview(gcode_path, head=120)


def _replan_paths_for_viz(iso_layers, spacing: float):
    """Re-run the path planner on each layer so we can plot the actual paths
    that were emitted (the pipeline keeps them only as side-effects in G-code)."""
    from reinforced_slicer.pathing.curved import plan_path_on_surface

    out = []
    for i, iso in enumerate(iso_layers):
        angle = 90.0 if i % 2 else 0.0
        out.append(plan_path_on_surface(iso, spacing=spacing, angle_deg=angle))
    return out


# --- Tab 4: kinematics inspector ----------------------------------------


def _run_kinematics_sweep(
    sweep_type: str, n_samples: int, smooth_singularities_flag: bool
) -> tuple[Any, str]:
    n = int(n_samples)
    poses: list[CutterPose] = []
    pos = np.array([0.0, 0.0, 50.0])
    if sweep_type == "Azimuth sweep at 45° tilt":
        phis = np.linspace(-np.pi, np.pi, n)
        for phi in phis:
            theta = np.pi / 4
            axis = np.array(
                [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)]
            )
            poses.append(CutterPose(position=pos, tool_axis=axis))
    elif sweep_type == "Tilt sweep at fixed azimuth":
        thetas = np.linspace(np.pi / 18, np.pi * 4 / 9, n)  # 10° to 80°
        for theta in thetas:
            phi = np.pi / 6
            axis = np.array(
                [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)]
            )
            poses.append(CutterPose(position=pos, tool_axis=axis))
    elif sweep_type == "Through-singularity crossing":
        n_half = n // 2
        thetas = np.concatenate(
            [np.linspace(np.pi / 6, 0.02, n_half), np.linspace(0.02, np.pi / 6, n - n_half)]
        )
        phis = np.concatenate(
            [np.full(n_half, -np.pi / 4), np.full(n - n_half, 3 * np.pi / 4)]
        )
        for t, p in zip(thetas, phis, strict=True):
            axis = np.array([np.sin(t) * np.cos(p), np.sin(t) * np.sin(p), np.cos(t)])
            poses.append(CutterPose(position=pos, tool_axis=axis))
    else:
        return None, f"Unknown sweep type: {sweep_type}"

    machine = AcTableMachine()
    joints = machine.solve_path(poses)
    if smooth_singularities_flag:
        segments = detect_singular_segments(machine, poses, threshold=0.1)
        if segments:
            joints = smooth_singularities(joints, segments, pad=3)

    singularity = [machine.singularity_distance(pose) for pose in poses]
    fig = joint_trajectory_plotly(poses, joints, singularity)

    # Summary text
    a_arr = np.array([j.rotary[0] for j in joints])
    c_arr = np.array([j.rotary[1] for j in joints])
    summary = (
        f"**{n} poses** swept.\n\n"
        f"- A range: [{np.degrees(a_arr.min()):.2f}°, {np.degrees(a_arr.max()):.2f}°]\n"
        f"- C range: [{np.degrees(c_arr.min()):.2f}°, {np.degrees(c_arr.max()):.2f}°]\n"
        f"- min singularity distance (sin A): {min(singularity):.4f}\n"
        f"- max |ΔC| per step: {float(np.max(np.abs(np.diff(c_arr)))):.4f} rad "
        f"({float(np.max(np.abs(np.diff(np.degrees(c_arr))))):.2f}°)\n"
        f"- singularity smoothing: **{'on' if smooth_singularities_flag else 'off'}**"
    )
    return fig, summary


# --- helpers --------------------------------------------------------------


def _format_stats(stats: dict[str, Any]) -> str:
    return "\n".join(f"- **{k}**: {v}" for k, v in stats.items())


def _gcode_preview(path: Path, head: int = 40, tail: int = 10) -> str:
    text = path.read_text()
    lines = text.splitlines()
    if len(lines) <= head + tail:
        return text
    return "\n".join(lines[:head] + [f"…  ({len(lines) - head - tail} lines elided)  …"] + lines[-tail:])


# --- App construction ----------------------------------------------------


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Reinforced-Slicer") as demo:
        gr.Markdown(
            "# Reinforced-Slicer\n"
            "Research-grade 5-axis slicer for continuous-fiber printing.  \n"
            "Tabs run in workflow order: **load → planar → curved → kinematics**."
        )

        mesh_state = gr.State(value=None)
        shoebox_state = gr.State(value=None)

        with gr.Tabs():
            with gr.Tab("1. Load & preview"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Upload a mesh")
                        upload = gr.File(
                            label="STL / OBJ / PLY",
                            file_types=[".stl", ".obj", ".ply"],
                            type="filepath",
                        )
                        load_status = gr.Markdown(
                            "Upload a mesh file (STL/OBJ/PLY) to begin."
                        )
                        gr.Markdown("---\n### …or build a synthetic cube")
                        cube_extent = gr.Slider(1.0, 100.0, value=20.0, step=1.0, label="Extent (mm)")
                        cube_subdiv = gr.Slider(2, 8, value=4, step=1, label="Subdivisions per axis")
                        cube_tilt = gr.Slider(-0.5, 0.5, value=0.3, step=0.05, label="Top tilt slope (Δz / Δx)")
                        cube_btn = gr.Button("Generate synthetic cube", variant="secondary")

                    with gr.Column(scale=2):
                        model3d = gr.Model3D(label="3D preview", height=500)
                        stats_md = gr.Markdown("*No mesh loaded yet.*")

                def on_upload(file_path):
                    mesh, msg, stats, viz_path = _load_uploaded_stl(file_path)
                    stats_md_val = _format_stats(stats) if stats else "*No stats — load failed.*"
                    return mesh, msg, stats_md_val, viz_path, None

                upload.change(
                    on_upload,
                    inputs=[upload],
                    outputs=[mesh_state, load_status, stats_md, model3d, shoebox_state],
                )

                def on_cube(extent, sub, tilt):
                    mesh, msg, stats, viz_path, shoebox = _make_synthetic_cube(extent, sub, tilt)
                    return mesh, msg, _format_stats(stats), viz_path, shoebox

                cube_btn.click(
                    on_cube,
                    inputs=[cube_extent, cube_subdiv, cube_tilt],
                    outputs=[mesh_state, load_status, stats_md, model3d, shoebox_state],
                )

            with gr.Tab("2. Planar slice (3-axis)"):
                with gr.Row():
                    with gr.Column(scale=1):
                        layer_h = gr.Slider(0.05, 1.0, value=0.2, step=0.05, label="Layer height (mm)")
                        infill_sp = gr.Slider(0.1, 2.0, value=0.4, step=0.05, label="Infill spacing (mm)")
                        infill_a = gr.Slider(0, 180, value=45, step=5, label="Infill angle (°)")
                        alt_angle = gr.Checkbox(value=True, label="Alternate angle every layer")
                        nozzle_t = gr.Slider(150, 280, value=210, step=5, label="Nozzle temp (°C)")
                        bed_t = gr.Slider(20, 110, value=60, step=5, label="Bed temp (°C)")
                        slice_btn = gr.Button("Slice", variant="primary")
                    with gr.Column(scale=2):
                        planar_plot = gr.Plot(label="Layer paths")
                        planar_stats = gr.Markdown("*Slice a mesh to see stats.*")
                        planar_gcode_file = gr.File(label="Download G-code", interactive=False)
                        planar_gcode_preview = gr.Code(
                            label="G-code preview", language=None, lines=12
                        )

                slice_btn.click(
                    _run_planar_slice,
                    inputs=[mesh_state, layer_h, infill_sp, infill_a, alt_angle, nozzle_t, bed_t],
                    outputs=[planar_plot, planar_stats, planar_gcode_file, planar_gcode_preview],
                )

            with gr.Tab("3. Curved layer (5-axis)"):
                gr.Markdown(
                    "Runs the M2c curved-layer pipeline: 3D CurviSlicer QP → iso-surfaces "
                    "→ paths-on-surfaces → 5-axis G-code through the AC-table kinematics."
                )
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Group():
                            gr.Markdown("**Tet mesh**")
                            curved_sub = gr.Slider(
                                2, 6, value=4, step=1,
                                label="Shoebox subdivisions (used if uploading a non-cube)",
                            )
                        with gr.Group():
                            gr.Markdown("**Layer + path**")
                            curved_layer_h = gr.Slider(0.5, 5.0, value=1.0, step=0.1, label="Layer height (mm)")
                            curved_spacing = gr.Slider(0.2, 4.0, value=1.0, step=0.1, label="Path spacing (mm)")
                        with gr.Group():
                            gr.Markdown("**CurviSlicer QP**")
                            tau_min = gr.Slider(0.1, 0.95, value=0.5, step=0.05, label="τ_min (min vertical stretch)")
                            tau_max = gr.Slider(1.1, 4.0, value=2.0, step=0.1, label="τ_max (max vertical stretch)")
                            flatness_w = gr.Slider(0.1, 100.0, value=10.0, step=0.5, label="Flatness weight")
                            smoothness_w = gr.Slider(1e-6, 1e-1, value=1e-4, step=1e-5, label="Smoothness weight")
                            use_target = gr.Checkbox(value=False, label="Override z_target")
                            z_target = gr.Slider(0.0, 100.0, value=20.0, step=0.5, label="z_target (mm)")
                        curved_btn = gr.Button("Slice (curved 5-axis)", variant="primary")
                    with gr.Column(scale=2):
                        curved_plot = gr.Plot(label="Curved layers + paths + sampled tool axes")
                        curved_obj = gr.Model3D(label="Curved-layer surfaces (download)", height=300)
                        curved_stats = gr.Markdown("*Run the curved slicer to see stats.*")
                        curved_gcode_file = gr.File(label="Download 5-axis G-code", interactive=False)
                        curved_gcode_preview = gr.Code(label="G-code preview", language=None, lines=12)

                curved_btn.click(
                    _run_curved_slice,
                    inputs=[
                        mesh_state, shoebox_state, curved_sub, curved_layer_h,
                        curved_spacing, tau_min, tau_max, flatness_w, smoothness_w,
                        z_target, use_target,
                    ],
                    outputs=[curved_plot, curved_stats, curved_obj, curved_gcode_file, curved_gcode_preview],
                )

            with gr.Tab("4. Kinematics inspector"):
                gr.Markdown(
                    "Drive synthetic tool-axis trajectories through the AC-table machine. "
                    "Useful for probing IK branch continuity and the GLT-2015 singularity smoother."
                )
                with gr.Row():
                    with gr.Column(scale=1):
                        sweep_type = gr.Radio(
                            choices=[
                                "Azimuth sweep at 45° tilt",
                                "Tilt sweep at fixed azimuth",
                                "Through-singularity crossing",
                            ],
                            value="Azimuth sweep at 45° tilt",
                            label="Trajectory",
                        )
                        n_samples = gr.Slider(20, 200, value=60, step=10, label="Path samples")
                        smooth_flag = gr.Checkbox(value=True, label="Apply GLT-2015 singularity smoother")
                        kin_btn = gr.Button("Run sweep", variant="primary")
                        kin_summary = gr.Markdown("*Pick a sweep type and run.*")
                    with gr.Column(scale=2):
                        kin_plot = gr.Plot(label="Joint trajectory + singularity distance")

                kin_btn.click(
                    _run_kinematics_sweep,
                    inputs=[sweep_type, n_samples, smooth_flag],
                    outputs=[kin_plot, kin_summary],
                )

        gr.Markdown(
            "---\n"
            "Reinforced-Slicer is research-grade; the curved-layer pipeline currently "
            "operates on a shoebox AABB approximation of uploaded meshes (real STL "
            "tetrahedralisation is deferred — see `mesh/__init__.py` for the licence "
            "situation). Synthetic cubes exercise the full algorithm faithfully."
        )

    return demo


__all__ = ["build_app"]
