{prompt}

Make it in Blender, working in the current directory.
- A Blender 5 instance is running for you with no window (background mode). Use it through the `blender`
  MCP tools: run Python (`bpy`) with execute_blender_code, and look things up with the API and manual
  search tools. Blender's working directory is the current directory. The scene starts as Blender's
  default one (a cube, a camera and a light).
- There is no window to screenshot. To check your work, render it to an image file and look at the image
  (render_thumbnail_to_path, render_viewport_to_path, or a render of the scene camera to a file).
  Keep renders quick: a single tool call may take at most 5 minutes. Save what you look at as .jpg rather
  than .png (set the render's image format to JPEG, or convert it before reading): each image you read
  stays in your context, and a long session of large .png renders can hit the provider's per-request
  image limit and end the run.
- Build it in Blender itself; don't write the model or the images any other way.
- Save the finished result in ./output/ (only what is in ./output/ is published):
  - the model or scene as one .glb file (glTF binary), shown on the site in an interactive 3D viewer:
    `bpy.ops.export_scene.gltf(filepath=..., export_format='GLB')`, without Draco or meshopt
    compression, at most 15 MB;
  - one or more final renders as .png or .jpg, at most 2 MB each, from camera angles you choose.
  At most 8 files in all.
- Tools available on this machine: {tools}. Don't install packages or download anything (no asset
  libraries or add-ons).
- Only create or edit files inside the current directory.
- End your final message with a line starting with `Blurb:`, then one to three sentences in the third
  person describing what you made for a visitor who will see it on the site: name the work if it has a
  name, and say what it is and what it does or is about. No file names, commands, instructions or claims
  about tests. For example: "Blurb: Ripple is a game that teaches players to spot online misinformation."
