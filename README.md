# PyWeek 30

This is an entry in the [PyWeek 30](https://pyweek.org/30/) challenge, with the theme "Castaway!".

[Click here to go to the PyWeek entry page.](https://pyweek.org/e/space-e/)


## Controls

* `f1` - Save screenshot (saves to the game's directory)
* `f2` - Save screenshot with LUT information for color grading
* `f3` - Toggle wireframe rendering of meshes
* `f4` - Toggle color grading
* `f5` - Hot reload game files (only available when running from source)
* `left mouse button` - Click to move, hold to start casting
* `right mouse button` - cancel current cast

## Configuration

The game can be configured by creating a `user.prc` file in the root of the project (i.e., next to `settings.prc`).
If this file is present, then it variables in it will take precedence over any other source.

Some useful variables (TODO: document how to use these):

* `win-size`
* `fullscreen`
* `click-hold-threshold`
* `cam-default-pos`
* `cam-charging-pos`

Here is an example of what a `user.prc` might look like:

```
win-size 1920 1080
fullscreen true
```

## Running from source

### Dependencies

* Python 3.7+
* Python packages in `requirements.txt`
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
