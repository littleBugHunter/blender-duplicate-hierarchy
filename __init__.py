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
            bpy.ops.object.duplicate(linked=True)
        else:
            bpy.ops.object.duplicate()
        
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
        """Duplicate selected objects and their children while preserving selection mapping"""
        # Store original selection and active object
        original_selection = context.selected_objects.copy()
        original_active = context.active_object
        
        if not original_selection:
            return None, "No valid objects selected"
        
        # Collect all objects to duplicate (selected objects + their children)
        all_objects_to_duplicate = []
        for obj in original_selection:
            all_children = self.get_all_children(obj, include_hidden=True)
            all_objects_to_duplicate.append(obj)
            all_objects_to_duplicate.extend(all_children)
        
        # Store original hide states and temporarily unhide all objects
        original_object_hide_states = {}
        original_collection_hide_states = {}
        original_layer_collection_hide_states = {}
        
        for obj in all_objects_to_duplicate:
            original_object_hide_states[obj] = {
                'hide_get': obj.hide_get(),
                'hide_viewport': obj.hide_viewport,
                'hide_select': obj.hide_select
            }
            obj.hide_set(False)
            obj.hide_viewport = False
            obj.hide_select = False
            
            # Also ensure collections containing the objects are visible
            for collection in obj.users_collection:
                if collection not in original_collection_hide_states:
                    original_collection_hide_states[collection] = {
                        'hide_viewport': collection.hide_viewport,
                        'hide_select': collection.hide_select
                    }
                    collection.hide_viewport = False
                    collection.hide_select = False
                
                # Also ensure layer collections are visible
                def find_layer_collection(layer_collection, target_collection):
                    """Recursively find layer collection by collection reference"""
                    if layer_collection.collection == target_collection:
                        return layer_collection
                    for child in layer_collection.children:
                        result = find_layer_collection(child, target_collection)
                        if result:
                            return result
                    return None
                
                layer_collection = find_layer_collection(context.view_layer.layer_collection, collection)
                if layer_collection and layer_collection not in original_layer_collection_hide_states:
                    original_layer_collection_hide_states[layer_collection] = {
                        'hide_viewport': layer_collection.hide_viewport,
                        'exclude': layer_collection.exclude
                    }
                    layer_collection.hide_viewport = False
                    layer_collection.exclude = False
        
        # Clear selection and select all objects to duplicate
        bpy.ops.object.select_all(action='DESELECT')
        for obj in all_objects_to_duplicate:
            obj.select_set(True)
        
        # Set the first originally selected object as active
        context.view_layer.objects.active = original_selection[0]
        
        # Duplicate all at once
        if linked_data:
            bpy.ops.object.duplicate('INVOKE_DEFAULT', False, linked=True)
        else:
            bpy.ops.object.duplicate('INVOKE_DEFAULT', False)
        
        # Get the duplicated objects
        duplicated_objects = context.selected_objects.copy()
        
        # Sort both lists alphabetically by name to ensure correct mapping
        objects_to_duplicate_sorted = sorted(all_objects_to_duplicate, key=lambda obj: obj.name)
        duplicated_objects_sorted = sorted(duplicated_objects, key=lambda obj: obj.name)
        
        # Create mapping from original to duplicated objects
        original_to_duplicated = {}
        for orig_obj, dup_obj in zip(objects_to_duplicate_sorted, duplicated_objects_sorted):
            original_to_duplicated[orig_obj] = dup_obj
        
        # Set hide states for duplicated objects to match their originals
        for orig_obj, dup_obj in original_to_duplicated.items():
            if orig_obj in original_object_hide_states:
                hide_state = original_object_hide_states[orig_obj]
                orig_obj.hide_set(hide_state['hide_get'])
                dup_obj.hide_set(hide_state['hide_get'])
                orig_obj.hide_viewport = hide_state['hide_viewport']
                dup_obj.hide_viewport = hide_state['hide_viewport']
                orig_obj.hide_select = hide_state['hide_select']
                dup_obj.hide_select = hide_state['hide_select']
        
        # Restore original collection hide states
        for collection, states in original_collection_hide_states.items():
            collection.hide_viewport = states['hide_viewport']
            collection.hide_select = states['hide_select']
        
        # Restore original layer collection hide states
        for layer_collection, states in original_layer_collection_hide_states.items():
            layer_collection.hide_viewport = states['hide_viewport']
            layer_collection.exclude = states['exclude']
        
        # Clear selection and apply original selection pattern to duplicated objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Deselect all original objects and select corresponding duplicated objects
        for orig_obj in original_selection:
            orig_obj.select_set(False)
            if orig_obj in original_to_duplicated:
                dup_obj = original_to_duplicated[orig_obj]
                dup_obj.select_set(True)
        
        # Set active object to the duplicate of the original active object
        if original_active and original_active in original_to_duplicated:
            context.view_layer.objects.active = original_to_duplicated[original_active]
        
        # Start grab/move mode for the duplicated objects
        bpy.ops.transform.translate('INVOKE_DEFAULT', False)
        
        return len(original_selection), None

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