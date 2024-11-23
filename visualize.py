from __future__ import annotations
import pyglet
import numpy as np
from shaders import batch, shader_update

#color fade based on intensity of new movement? like if a sudden thing happens it should be brighter and otherwise be fading
    #keep track of change in db wrt time, adjust brightness based on amount of change
#combine bar_update and line_update, theres a lot of duplicate lines

WINDOW_WIDTH, WINDOW_HEIGHT = 1400, 540
EDGE_XPAD = 10
EDGE_YPAD = 5

ITEM_YSCALE = 4

ITEM_COLOR = (142, 96, 168)
BACKGROUND_COLOR = (26, 40, 86)

FPS = 30.0
MAX_DELAY = 0.05

def display_window(audio_path: str, db_arr: np.ndarray, display_mode: str) -> None:
    audio = pyglet.media.load(audio_path)
    window = pyglet.window.Window(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    background = pyglet.shapes.Rectangle(x=0, y=0, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, color=BACKGROUND_COLOR)

    # label = pyglet.text.Label('Hello, world',
    #                         font_name='Times New Roman',
    #                         font_size=36,
    #                         x=window.width//2, y=window.height//2,
    #                         anchor_x='center', anchor_y='center')

    if display_mode == "bar":
        objects = bar_make(db_arr)
        pyglet.clock.schedule_interval(Updater.bar_update, (1 / FPS) / 1.4, objects, db_arr)
        pyglet.clock.schedule_interval(shader_update, (1 / FPS) / 1.4)
    elif display_mode == "line":
        objects = line_make(db_arr)
        pyglet.clock.schedule_interval(Updater.line_update, (1 / FPS) / 1.4, objects, db_arr)
    else:
        msg = "Invalid display mode. Choose either 'bar' or 'line'"
        raise ValueError(msg)

    @window.event
    def on_draw() -> None:
        window.clear()
        background.draw()
        batch.draw()
        for o in objects:
            o.draw()

    audio.play()
    pyglet.app.run()


#==============#
# Bar Graphing #
#==============#

def bar_make(db_arr: np.ndarray) -> list[pyglet.shapes.Rectangle]:
    item_spacing = 1
    bar_width = int(WINDOW_WIDTH - (2 * EDGE_XPAD) - ((db_arr.shape[1] - 1) * item_spacing)) / db_arr.shape[1]
    #To have maximum volume take up entire window:
    #BAR_YSCALE = (WINDOW_HEIGHT - (2 * EDGE_YPAD)) / 80
    bars = []
    for bar_index in range(db_arr.shape[1]):
        bars.append(pyglet.shapes.Rectangle(x=EDGE_XPAD + (bar_index * item_spacing) + (bar_index * bar_width),
                                            y=EDGE_YPAD, width=bar_width, height=1, color=ITEM_COLOR))
    return bars


#===============#
# Line Graphing #
#===============#

def line_make(db_arr: np.ndarray) -> list[pyglet.shapes.Line]:
    line_xlen = (WINDOW_WIDTH - (2 * EDGE_XPAD)) / db_arr.shape[1]
    lines = []
    for i in range(len(db_arr[1]) - 1):
        x = EDGE_XPAD + (i * line_xlen)
        x2 = EDGE_XPAD + ((i+1) * line_xlen)
        lines.append(pyglet.shapes.Line(x=x, y=EDGE_YPAD, x2=x2, y2=EDGE_YPAD, width=2.0, color=ITEM_COLOR))

    return lines


class Updater:
    vid_frame = 0
    vid_total_time = 0
    real_total_time = 0

    @classmethod
    def bar_update(cls, dt: int, bars: list[pyglet.shapes.Rectangle], db_arr: np.ndarray) -> None:
        time_diff = Updater.get_time_gap(dt)

        if cls.vid_frame < db_arr.shape[0]:
            for bar_index, bar in enumerate(bars):
                bar.height = db_arr[cls.vid_frame][bar_index] * ITEM_YSCALE
            cls.vid_frame += 1

        if time_diff > MAX_DELAY:
            Updater.bar_update(0, bars, db_arr)

    @classmethod
    def line_update(cls, dt: int, lines: list[pyglet.shapes.Line], db_arr: np.ndarray) -> None:
        time_diff = Updater.get_time_gap(dt)

        if cls.vid_frame < db_arr.shape[0]:
            for line_index, line in enumerate(lines):
                line.y = db_arr[cls.vid_frame][line_index] * ITEM_YSCALE
                line.y2 = db_arr[cls.vid_frame][line_index+1] * ITEM_YSCALE
            cls.vid_frame += 1

        if time_diff > MAX_DELAY:
            Updater.line_update(0, lines, db_arr)

    @classmethod
    def get_time_gap(cls, dt: int) -> int:
        cls.vid_total_time += dt
        cls.real_total_time += (1 / FPS)
        return cls.vid_total_time - cls.real_total_time
