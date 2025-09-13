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
        
        # Sort both lists alphabetically by name to ensure correct mapping
        objects_to_duplicate_sorted = sorted(objects_to_duplicate, key=lambda obj: obj.name)
        duplicated_objects_sorted = sorted(duplicated_objects, key=lambda obj: obj.name)
        
        # Create mapping from original to duplicated objects
        original_to_duplicated = {}
        duplicated_to_original = {}
        for orig_obj, dup_obj in zip(objects_to_duplicate_sorted, duplicated_objects_sorted):
            original_to_duplicated[orig_obj] = dup_obj
            duplicated_to_original[dup_obj] = orig_obj
        
        return duplicated_objects, original_to_duplicated, duplicated_to_original
    
    def duplicate_with_selection_mapping(self, context, linked_data=False):
        """Duplicate filtered objects and preserve selection mapping"""
        # Store original selection and active object
        original_selection = context.selected_objects.copy()
        original_active = context.active_object
        
        # Get filtered selection (remove children of selected objects)
        selected_objects = context.selected_objects.copy()
        filtered_objects = self.filter_selection(selected_objects)
        
        if not filtered_objects:
            return None, "No valid objects selected"
        
        all_mappings = {}
        all_duplicated = []
        
        # Duplicate each filtered object with its hierarchy
        for obj in filtered_objects:
            duplicated_objects, original_to_duplicated, duplicated_to_original = self.duplicate_hierarchy(obj, linked_data=linked_data)
            all_mappings.update(original_to_duplicated)
            all_mappings.update(duplicated_to_original)
            all_duplicated.extend(duplicated_objects)
        
        # Clear selection and deselect all original objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Apply original selection pattern to duplicated objects
        for dup_obj in all_duplicated:
            if dup_obj in all_mappings:
                orig_obj = all_mappings[dup_obj]
                dup_obj.select_set(orig_obj in original_selection)
        
        if original_active and original_active in all_mappings:
            context.view_layer.objects.active = all_mappings[original_active]
        
        # Start grab/move mode for the duplicated objects
        bpy.ops.transform.translate('INVOKE_DEFAULT')
        
        return len(filtered_objects), None

class OBJECT_OT_duplicate_with_children_cloned(OBJECT_OT_duplicate_with_children_base, Operator):
    """Duplicate selected objects with all their children (cloned data)"""
    bl_idname = "object.duplicate_with_children_cloned"
    bl_label = "Duplicate with Children (Cloned)"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.mode == 'OBJECT'
    
    def execute(self, context):
        result, error = self.duplicate_with_selection_mapping(context, linked_data=False)
        
        if error:
            self.report({'WARNING'}, error)
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Duplicated {result} object(s) with children")
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
        result, error = self.duplicate_with_selection_mapping(context, linked_data=True)
        
        if error:
            self.report({'WARNING'}, error)
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Duplicated {result} object(s) with children (linked)")
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