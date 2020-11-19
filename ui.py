import bpy

class NODECAPTURE_PT_CaptureNodeTreePanel(bpy.types.Panel):
    bl_label = "Node Capture"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "View"

    def draw(self, context):
        layout = self.layout
        layout.operator("NODECAPTURE_OT_capturenodetree")
        