import bpy
import bmesh
from bpy.types import Operator
from bpy.props import BoolProperty

bl_info = {
    "name": "Duplicate with Children",
    "author": "Paul Nasdalack",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "3D Viewport > Object > Duplicate with Children",
    "description": "Duplicate objects with all their children",
    "category": "Object",
}

class OBJECT_OT_duplicate_with_children_base:
    """Base class for duplicate with children operators"""
    
    def get_all_children(self, obj, include_hidden=True):
        """Recursively get all children of an object"""
        children = []
        for child in obj.children:
            if include_hidden or not child.hide_get():
                children.append(child)
                children.extend(self.get_all_children(child, include_hidden))
        return children
    
    def filter_selection(self, selected_objects):
        """Filter out objects that are children of other selected objects"""
        filtered = []
        for obj in selected_objects:
            is_child_of_selected = False
            # Check if this object is a child of any other selected object
            parent = obj.parent
            while parent:
                if parent in selected_objects:
                    is_child_of_selected = True
                    break
                parent = parent.parent
            
            if not is_child_of_selected:
                filtered.append(obj)
        
        return filtered
    
    def duplicate_hierarchy(self, obj, linked_data=False):
        """Duplicate an object and all its children"""
        # Store original selection and active object
        original_selection = bpy.context.selected_objects.copy()
        original_active = bpy.context.active_object
        
        # Get all children (including hidden ones)
        all_children = self.get_all_children(obj, include_hidden=True)
        objects_to_duplicate = [obj] + all_children
        
        # Clear selection and select objects to duplicate
        bpy.ops.object.select_all(action='DESELECT')
        for obj_to_dup in objects_to_duplicate:
            obj_to_dup.select_set(True)
        
        # Set the root object as active
        bpy.context.view_layer.objects.active = obj
        
        # Duplicate based on type
        if linked_data:
            bpy.ops.object.duplicate_move_linked()
        else:
            bpy.ops.object.duplicate_move()
        
        # Get the duplicated objects
        duplicated_objects = bpy.context.selected_objects.copy()
        
        return duplicated_objects

class OBJECT_OT_duplicate_with_children_cloned(OBJECT_OT_duplicate_with_children_base, Operator):
    """Duplicate selected objects with all their children (cloned data)"""
    bl_idname = "object.duplicate_with_children_cloned"
    bl_label = "Duplicate with Children (Cloned)"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.mode == 'OBJECT'
    
    def execute(self, context):
        # Get filtered selection (remove children of selected objects)
        selected_objects = context.selected_objects.copy()
        filtered_objects = self.filter_selection(selected_objects)
        
        if not filtered_objects:
            self.report({'WARNING'}, "No valid objects selected")
            return {'CANCELLED'}
        
        all_duplicated = []
        
        # Duplicate each filtered object with its hierarchy
        for obj in filtered_objects:
            duplicated = self.duplicate_hierarchy(obj, linked_data=False)
            all_duplicated.extend(duplicated)
        
        # Clear selection and select all duplicated objects
        bpy.ops.object.select_all(action='DESELECT')
        for dup_obj in all_duplicated:
            dup_obj.select_set(True)
        
        # Set the first duplicated object as active
        if all_duplicated:
            context.view_layer.objects.active = all_duplicated[0]
        
        self.report({'INFO'}, f"Duplicated {len(filtered_objects)} object(s) with children")
        return {'FINISHED'}

class OBJECT_OT_duplicate_with_children_linked(OBJECT_OT_duplicate_with_children_base, Operator):
    """Duplicate selected objects with all their children (linked data)"""
    bl_idname = "object.duplicate_with_children_linked"
    bl_label = "Duplicate with Children (Linked)"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.mode == 'OBJECT'
    
    def execute(self, context):
        # Get filtered selection (remove children of selected objects)
        selected_objects = context.selected_objects.copy()
        filtered_objects = self.filter_selection(selected_objects)
        
        if not filtered_objects:
            self.report({'WARNING'}, "No valid objects selected")
            return {'CANCELLED'}
        
        all_duplicated = []
        
        # Duplicate each filtered object with its hierarchy
        for obj in filtered_objects:
            duplicated = self.duplicate_hierarchy(obj, linked_data=True)
            all_duplicated.extend(duplicated)
        
        # Clear selection and select all duplicated objects
        bpy.ops.object.select_all(action='DESELECT')
        for dup_obj in all_duplicated:
            dup_obj.select_set(True)
        
        # Set the first duplicated object as active
        if all_duplicated:
            context.view_layer.objects.active = all_duplicated[0]
        
        self.report({'INFO'}, f"Duplicated {len(filtered_objects)} object(s) with children (linked)")
        return {'FINISHED'}

def menu_func_cloned(self, context):
    self.layout.operator(OBJECT_OT_duplicate_with_children_cloned.bl_idname)

def menu_func_linked(self, context):
    self.layout.operator(OBJECT_OT_duplicate_with_children_linked.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_duplicate_with_children_cloned)
    bpy.utils.register_class(OBJECT_OT_duplicate_with_children_linked)
    bpy.types.VIEW3D_MT_object.append(menu_func_cloned)
    bpy.types.VIEW3D_MT_object.append(menu_func_linked)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_duplicate_with_children_cloned)
    bpy.utils.unregister_class(OBJECT_OT_duplicate_with_children_linked)
    bpy.types.VIEW3D_MT_object.remove(menu_func_cloned)
    bpy.types.VIEW3D_MT_object.remove(menu_func_linked)

if __name__ == "__main__":
    register()