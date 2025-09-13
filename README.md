# Duplicate Hierarchy

A Blender addon that allows you to duplicate objects along with all their children (hierarchy) while preserving the original selection pattern.

## Installation

1. Download the addon files
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install...` and select the addon zip file or folder
4. Enable the "Duplicate Hierarchy" addon in the list

## Usage

### Access Methods

The addon adds two operators to the Object menu:

- **3D Viewport > Object > Duplicate Hierarchy**
- **3D Viewport > Object > Duplicate Hierarchy (Linked)**

### How It Works

1. Select one or more parent objects
2. Run either duplicate command
3. The addon will:
   - Duplicate the selected objects and all their children (hierarchy)
   - Preserve the original selection pattern on the duplicates
   - Automatically enter move mode for positioning
   - Maintain original visibility states of hidden objects

## Version History

### v1.0
- Initial release
- Basic duplicate hierarchy functionality
- Selection pattern preservation
- Hidden object support
- Cloned and linked data modes