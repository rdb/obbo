# PyWeek 30

This is an entry in the [PyWeek 30](https://pyweek.org/30/) challenge, with the theme "Castaway!".

[Click here to go to the PyWeek entry page.](https://pyweek.org/e/space-e/)


## Controls

* `f1` - Save screenshot (saves to the game's directory)
* `f3` - Toggle wireframe rendering of meshes
* `f5` - Hot reload game files (only available when running from source)
* `left mouse button` - Click to move, hold to start casting
* `right mouse button` - cancel current cast

## Configuration

The game can be configured by creating a `user.prc` file in the root of the project (i.e., next to `settings.prc`).
If this file is present, then it variables in it will take precedence over any other source.

Some useful variables:

* `win-size` - two numbers to control the resolution (e.g., `win-size 1280 720`)
* `fullscreen` - `true`/`false` to control fullscreen mode (e.g., `fullscreen true`)
* `click-hold-threshold` - a floating point value for how long the mouse needs to remain pressed (in seconds) to be considered "held" (e.g., `click-hold-threshold 0.4`)
* `confine-mouse` - `true`/`false` to control if the mouse cursor can leave the window boundaries (e.g., `confine-mouse false`)
* `skip-main-menu` - `true`/`false` to skip the main menu, intro cutscene, etc. and jump straight to the game (e.g., `skip-main-menu true`)
* `show-frame-rate-meter` - `true`/`false` to display an FPS counter in the top right of the screen (e.g., `show-frame-rate-meter true`)
* `potato-mode` - `true`/`false` try to turn down visuals to run on low-end hardware (e.g., `potato-mode true`)

Here is an example of what a `user.prc` might look like:

```
win-size 1920 1080
fullscreen true
```

## Running from source

### Dependencies

* Python 3.7+
* Python packages in `requirements.txt`
* `blend2bamex` entry point for `pman` (run `pip install -e .` to get this)
* Blender 2.90 (preferably on the system PATH)
* [limeade](https://pypi.org/project/limeade/) (optional, allows hot reloading of source code)

### Run the game


To run, simply cd to the directory containing the game and type:

```
python run_game.py
```

## Acknowledgements

TODO

Many thanks to @lordmauve and all the other PyWeek participants for a great challenge!
