# The Cool Route

A short routing game about checking in on neighbors during a heat wave. Deliver water to every household across three rounds before daylight runs out.

## Run

Open this directory in Godot 4.7.2 and press **F6** with the main scene open, or press **F5** from anywhere in the editor. You can also run `godot --path .` from this directory.

Click or tap a map tile or a household in the list to follow a route. Arrow keys and WASD move one tile at a time. Fountains refill your three-bottle carrier. Shade uses one unit of daylight per tile and sun uses two. Households open shaded stops after you deliver their water. Those stops stay open in later rounds.

Press **Z** to undo a route, **R** to restart the current day, or **H** to open the field guide. The help and day controls also work by mouse or touch.

Art and sound are generated in Godot. The project uses the Compatibility renderer and runs on a single thread.
