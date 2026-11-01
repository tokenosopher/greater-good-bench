# Common Ground

A complete, six-week neighborhood strategy game about listening, access, and making sure nobody is left behind. Built for Godot 4.7.2 with the GL Compatibility renderer, without external assets, plugins, downloads, or threads.

## Run

Open `project.godot` in Godot 4.7.2 and press **F6** on `main.tscn`, or **F5** to run the project. From this directory: `godot --path .`

Click a home to listen to its residents. Click an empty lot to build a service. Nearby homes receive its benefits; the gold preview shows who will benefit before you spend. Buildings can be upgraded. Advance through six weeks, adapting to each week's circumstances. Bring **every household to at least 70% support** by the end of week six. You receive three actions per week; unused funds carry over and each new week brings four more funds. Listening costs one action, adds one fund, and permanently helps a household's most pressing need. Your latest action can be undone until you advance the week.

**Controls:** mouse to select and act; arrow keys to move between lots; **1–5** to build on a selected empty lot; **L** to listen; **U** to upgrade; **Z** to undo; **Space** to advance the week; **H** or **?** for help; **M** for sound; **Escape** to close a dialog. All keyboard shortcuts appear in the game. The help screen explains coverage, priorities, and the final assessment.

Original isometric buildings, trees, people, interface, and animation are drawn in code. Sound effects are synthesized locally. The project is ready for a web export using Godot's single-threaded export setting. No export is included.

## Check

`godot --headless --path . --editor --quit`

`godot --headless --path . --script res://tests/smoke.gd`
