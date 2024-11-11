# smcpeak-addon.py
"""Blender add-on with misc functions I want."""

bl_info = {
    "name": "smcpeak Add-on",
    "blender": (4, 1, 0),
    "category": "Object",
}

import bpy
import os


def get_calibri_font():
    """Return the "Calibri Bold" font, loading it if needed."""

    font_name = 'Calibri Bold'

    # Load it if necessary.
    if not font_name in bpy.data.fonts:
        print(f"Loading font: {font_name}.")
        bpy.ops.font.open(filepath="C:\\WINDOWS\\Fonts\\calibrib.ttf")

    return bpy.data.fonts[font_name]


def add_text_strip(context, duration):
    """Add a text strip starting at the current frame and lasting for
    `duration` frames.  Return the strip."""

    frame_num = context.scene.frame_current
    bpy.ops.sequencer.effect_strip_add(
        type='TEXT',
        frame_start=frame_num,
        frame_end=frame_num+duration)
    strip = context.active_sequence_strip
    strip.use_shadow = True
    return strip


def render_frame(context):
    """Render the current frame to a file named "frame-NNN.png" in the
    same directory as the main output file, where NNN is the frame
    number.  Return the new file name."""

    # Get the output directory of the main output file.
    out_dir = os.path.dirname(context.scene.render.filepath)

    # Name the new file according to the current frame number.
    frame_num = context.scene.frame_current
    new_filepath = os.path.join(out_dir, f"frame-{frame_num}.png")

    # Save the current render settings so we can restore them at the end.
    orig_filepath = context.scene.render.filepath
    orig_file_format = context.scene.render.image_settings.file_format

    try:
        # Modify the settings to write a single image file.
        context.scene.render.filepath = new_filepath
        context.scene.render.image_settings.file_format = "PNG"

        # Render the image.
        bpy.ops.render.render(write_still=True)

    finally:
        try:
            # Try to restore the scene render settings.
            context.scene.render.filepath = orig_filepath
            context.scene.render.image_settings.file_format = orig_file_format
        except Exception as e:
            # Log, but swallow so whatever the original exception was
            # can propagate and be seen in the UI.
            print(f"Exn while restoring values: {e}")

    return new_filepath


def add_parry_timer_inset(context, n):
    """Assuming that the current frame shows a parry attempt on the
    deciding frame, freeze the portion showing the parry timer and
    persistently show it for 4 seconds.  `n` is the position of this
    timer freeze-frame, where 0 is the first.  It is needed when we
    want to show more than one onscreen at once."""

    # Save the current frame to a file.
    new_filepath = render_frame(context)

    # Get some details.
    basename = os.path.basename(new_filepath)
    directory = os.path.dirname(new_filepath)
    frame_num = context.scene.frame_current

    # Add a small piece of that frame as a lingering inset.
    bpy.ops.sequencer.image_strip_add(
        directory=directory,
        files=[{"name":basename}],
        relative_path=True,
        show_multiview=False,
        frame_start=frame_num,
        frame_end=frame_num+120,
        fit_method='ORIGINAL',
        set_view_transform=False)
    img = context.active_sequence_strip

    # Crop to just the parry timer.
    img.crop.min_x = 1166
    img.crop.max_x = 57
    img.crop.min_y = 665
    img.crop.max_y = 28

    # Move it down to below the main gamepad viewer area.
    img.transform.offset_y = -(150 + 50*n)

    # Add the text label.
    label = add_text_strip(context, 120)

    # Adjust its details.
    label.font_size = 20
    label.align_x = 'RIGHT'
    label.location[0] = 0.9            # x
    label.location[1] = 0.74 - 0.07*n  # y

    font = get_calibri_font()
    if font:
        label.font = font


def add_attempt_number(context):
    """Add a text box showing the current attempt number."""

    # Make a text strip from now to the end.
    remaining_frames = context.scene.frame_end - context.scene.frame_current
    label = add_text_strip(context, remaining_frames)
    label.font_size = 40
    label.align_x = 'RIGHT'
    label.location[0] = 0.98   # x
    label.location[1] = 0.12   # y

    # Start the counter with 1, and I will manually split the strip and
    # increment the count from there.
    label.text = "1"

    font = get_calibri_font()
    if font:
        label.font = font


def ripple_delete(context):
    """Delete the currently selected strips, then move everything that
    is after them left by their width."""

    # The active strip might not be among the selected strips, so focus
    # on what is selected.
    if len(context.selected_sequences) == 0:
        raise RuntimeError("No selected strips.")

    first_sel = context.selected_sequences[0]

    # Assume all selected strips have the same start and duration.
    start = first_sel.frame_final_start
    duration = first_sel.frame_final_duration

    # Delete selected strips.
    bpy.ops.sequencer.delete()

    # Move the current frame to where they started.
    context.scene.frame_current = start

    # Select everything after the current frame.
    bpy.ops.sequencer.select_side_of_frame(
        side='RIGHT')

    # Move them to the left.
    bpy.ops.transform.seq_slide(
        value=(-duration, 0),
        snap=False)


def print_text_strips(context):
    """Print to the system console the text of every selected text,
    ordered by start frame strip."""

    strips = context.selected_editable_sequences
    strips = sorted(strips, key=lambda strip: strip.frame_final_start)
    count = len(strips)

    print(f"---- {count} text strips ----")
    for strip in strips:
        if strip.type == 'TEXT':
            print(strip.text)


# ----------------------------- operators ------------------------------
class RenderFrameOperator(bpy.types.Operator):
    """Render the current frame to a file."""
    bl_idname = "smcpeak.render_frame"
    bl_label = "Render Frame Operator"

    def execute(self, context):
        render_frame(context)
        return {'FINISHED'}


class AddParryTimerInset0Operator(bpy.types.Operator):
    """Add a parry timer inset based on the current frame in slot 0."""
    bl_idname = "smcpeak.add_parry_timer_inset0"
    bl_label = "Add Parry Timer Inset Slot 0 Operator"

    def execute(self, context):
        add_parry_timer_inset(context, 0)
        return {'FINISHED'}


class AddParryTimerInset1Operator(bpy.types.Operator):
    """Add a parry timer inset based on the current frame in slot 1."""
    bl_idname = "smcpeak.add_parry_timer_inset1"
    bl_label = "Add Parry Timer Inset Slot 1 Operator"

    def execute(self, context):
        add_parry_timer_inset(context, 1)
        return {'FINISHED'}


class AddAttemptNumberOperator(bpy.types.Operator):
    """Add a text box showing the current attempt number."""
    bl_idname = "smcpeak.add_attempt_number"
    bl_label = "Add Attempt Number Operator"

    def execute(self, context):
        add_attempt_number(context)
        return {'FINISHED'}


class RippleDeleteOperator(bpy.types.Operator):
    """Delete currently selected strips and move everything currently to
    the right of them left by the deleted strips' duration, thus closing
    the gap."""
    bl_idname = "smcpeak.ripple_delete"
    bl_label = "Ripple Delete Operator"

    def execute(self, context):
        ripple_delete(context)
        return {'FINISHED'}


class PrintTextStripsOperator(bpy.types.Operator):
    """Print all selected text strips' text to the system console."""
    bl_idname = "smcpeak.print_text_strips"
    bl_label = "Print text strips to the console"

    def execute(self, context):
        print_text_strips(context)
        return {'FINISHED'}


# ---------------------------- registration ----------------------------
def register():
    bpy.utils.register_class(RenderFrameOperator)
    bpy.utils.register_class(AddParryTimerInset0Operator)
    bpy.utils.register_class(AddParryTimerInset1Operator)
    bpy.utils.register_class(AddAttemptNumberOperator)
    bpy.utils.register_class(RippleDeleteOperator)
    bpy.utils.register_class(PrintTextStripsOperator)


def unregister():
    bpy.utils.unregister_class(RenderFrameOperator)
    bpy.utils.unregister_class(AddParryTimerInset0Operator)
    bpy.utils.unregister_class(AddParryTimerInset1Operator)
    bpy.utils.unregister_class(AddAttemptNumberOperator)
    bpy.utils.unregister_class(RippleDeleteOperator)
    bpy.utils.unregister_class(PrintTextStripsOperator)


if __name__ == "__main__":
    register()
