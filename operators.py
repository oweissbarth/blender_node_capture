import bpy
from mathutils import Vector
import numpy as np
import math

class NODECAPTURE_OT_CaptureNodeTree(bpy.types.Operator):
    bl_idname = "nodecapture.capturenodetree"
    bl_label = "CaptureNodeTree"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):

        node_tree = context.space_data.edit_tree

        current_center = node_tree.view_center

        min_val, max_val = self.get_bounding_box(node_tree)

        region_min= Vector(context.region.view2d.view_to_region(min_val.x, min_val.y, clip=False))
        region_max= Vector(context.region.view2d.view_to_region(max_val.x, max_val.y, clip=False))

        region_center = Vector((context.region.width/2, context.region.height/2))

        to_min =  region_min - region_center

        bpy.ops.view2d.pan(deltax=to_min.x, deltay=to_min.y)
        
        size = region_max - region_min
         
        padding = 50
        steps_x = math.ceil(size.x / (context.region.width-2*padding))+1
        steps_y = math.ceil(size.y / (context.region.height-2*padding))+1
        
        win = context.window_manager

        total_steps = 2*steps_x*steps_y
        win.progress_begin(0, 100)

        stepsize_x = context.region.width-2*padding
        stepsize_y = context.region.height-2*padding
        section_size_x = context.region.width - 2*padding
        section_size_y = context.region.height - 2*padding
        screenshot_size_x = context.region.width
        screenshot_size_y = context.region.height

        # Create Screenshots
        for y in range(steps_y):
            for x in range(steps_x):
                bpy.ops.screen.screenshot(filepath=bpy.app.tempdir+"capture_nodes_"+str(x)+"_"+str(y)+".png", full=False)
                bpy.ops.view2d.pan(deltax=stepsize_x, deltay=0)
                win.progress_update((y*steps_x + x)*100/total_steps)
            bpy.ops.view2d.pan(deltax=-steps_x*section_size_x, deltay=section_size_y)

        
        # Assemble Screenshots
        canvas_img = bpy.data.images.new("CaptureNodes", steps_x*section_size_x, steps_y*section_size_y)
        canvas = np.empty((steps_x*section_size_x, steps_y*section_size_y, 4), dtype=np.float32)
        temp = np.empty((screenshot_size_x) * (screenshot_size_y)* 4, dtype=np.float32)

        for y in range(steps_y):
            for x in range(steps_x):
                img = bpy.data.images.load(bpy.app.tempdir+"capture_nodes_"+str(x)+"_"+str(y)+".png")
                offset_x = x*section_size_x
                offset_y = y*section_size_y

                img.pixels.foreach_get(temp)
                temp_img = np.swapaxes(temp.reshape((screenshot_size_y, screenshot_size_x, 4)), 0, 1)

                canvas_start_x = offset_x
                canvas_end_x = offset_x+section_size_x

                canvas_start_y = offset_y
                canvas_end_y = offset_y+section_size_y

                section_start_x = padding
                section_end_x = section_size_x+padding

                section_start_y = padding
                section_end_y = section_size_y + padding

                canvas[canvas_start_x: canvas_end_x, canvas_start_y:canvas_end_y, :] = temp_img[section_start_x:section_end_x, section_start_y:section_end_y, :]

                bpy.data.images.remove(img)
                win.progress_update((steps_x*steps_y + y*steps_x + x)*100/total_steps)
        canvas_img.pixels.foreach_set( np.swapaxes(canvas, 0, 1).ravel())

        canvas_img.file_format = "PNG"
        canvas_img.filepath_raw = self.filepath
        canvas_img.save()

        # restore UI
        context.area.spaces.active.show_region_ui = self.region_ui_before
        context.area.spaces.active.show_region_header = self.region_header_before
        context.area.spaces.active.show_region_toolbar = self.region_toolbar_before

        bpy.data.images.remove(canvas_img)

        win.progress_end()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        #bpy.ops.nodecapture.hideui()
   
        self.region_ui_before = context.area.spaces.active.show_region_ui
        self.region_header_before = context.area.spaces.active.show_region_header
        self.region_toolbar_before = context.area.spaces.active.show_region_toolbar

        context.area.spaces.active.show_region_ui = False
        context.area.spaces.active.show_region_header = False
        context.area.spaces.active.show_region_toolbar = False
        

        return {'RUNNING_MODAL'}


    @staticmethod
    def get_bounding_box(node_tree):
        min_val = Vector((float("inf"),float("inf")))
        max_val = Vector((-float("inf"), -float("inf")))
        for n in node_tree.nodes:
            if n.location.x < min_val.x:
                min_val.x = n.location.x
            if n.location.y < min_val.y:
                min_val.y = n.location.y
            
            if n.location.x > max_val.x:
                max_val.x = n.location.x
            if n.location.y > max_val.y:
                max_val.y = n.location.y
        return min_val, max_val