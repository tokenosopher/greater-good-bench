# Common Ground

A short, turn-based game about sharing one lake with four neighbours.
Each season you choose how many fish to take and one other thing to do:
rest, share, watch, or propose a limit. The lake grows back in proportion
to what is left in it. There is no score for you alone; the game is scored
on how the whole village is doing after twenty seasons, with extra weight
on whoever is worst off.

Your neighbours each model a common response to a shared resource: one is
steady, one copies the crowd, one grabs because nobody ever shared with him,
and one panics when the water drops. They remember what you do. The point of
playing is to feel, in a few minutes, that visible agreements, keeping your
own promise first, and sharing when someone is short are what make a commons
work. The ending gives you one small real-world thing to try.

## Run it

Requires Godot 4.7.2 (the project uses the GL Compatibility renderer and no
thread support, so it also works as a web export).

From this directory:

    godot --path .

Or open `project.godot` in the Godot editor and press Play. The main scene is
`scenes/Main.tscn`.

## Files

- `scripts/Main.gd` - game loop, UI, scoring, intro and ending screens
- `scripts/Household.gd` - the four neighbour behaviours and the player
- `scripts/LakeView.gd` - the drawn lake and its fish
- `scripts/Face.gd` - the small drawn faces on the household cards

No external assets or plugins are used.
