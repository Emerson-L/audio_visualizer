from __future__ import annotations
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import animation
from scipy import interpolate
from pydub import AudioSegment
from pydub.playback import play
import threading

#color fade based on intensity of new movement? like if a sudden thing happens it should be brighter and otherwise be fading
    #keep track of change in db wrt time, adjust brightness based on amount of change
#combine bar_update and line_update, theres a lot of duplicate lines
#fix animation being ~0.12s behind

WINDOW_WIDTH, WINDOW_HEIGHT = 12, 4
EDGE_XPAD, EDGE_YPAD = 20, 10

ITEM_SPACING = 8 #normally 8
ITEM_YSCALE = 4

ITEM_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (0, 0, 0)

FPS = 25.0 #1000 / FPS must be a whole number
MAX_DELAY = 0.05

#def display_window(audio_path: str, db_array: np.ndarray, display_mode: str) -> None:

def display_window(audio_path: str, db_array: np.ndarray, display_mode: str) -> None:
    #audio = pyglet.media.load(audio_path)
    #window = pyglet.window.Window(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    #background = pyglet.shapes.Rectangle(x=0, y=0, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, color=BACKGROUND_COLOR)

    audio = AudioSegment.from_file(audio_path)
    audio_thread = threading.Thread(target=play, args=(audio,))
    audio_thread.daemon = True
    #audio_length = audio.duration_seconds

    x_size = db_array.shape[0]

    plt.rcParams["figure.figsize"] = [WINDOW_WIDTH, WINDOW_HEIGHT]
    ymax = np.max(db_array)

    fig = plt.figure()
    ax = plt.axes(xlim=(0, 1), ylim=(0, ymax))
    line, = ax.plot([], [], lw=2)

    def init() -> mpl.lines.Line2D:
        line.set_data([], [])
        return line,

    x = np.linspace(0, 1, x_size)
    def animate(i: int) -> mpl.lines.Line2D:
        #global audio_start_time
        if i == 0:
            audio_thread.start()
            #audio_start_time = time.perf_counter()

        y = db_array[:,i]
        spline = interpolate.make_interp_spline(x, y)

        xpoints = x
        ypoints = spline(xpoints)

        line.set_data(xpoints, ypoints)

        #timing test
        #audio_time = time.perf_counter() - audio_start_time
        #animation_time = i * (1 / FPS)
        #print("timediff: " + str(animation_time - audio_time))

        return line,

    ani = animation.FuncAnimation(fig, animate, init_func=init, frames=db_array.shape[1], interval=(1/FPS)*1000, blit=True)
    plt.show()



    # label = pyglet.text.Label('Hello, world',
    #                         font_name='Times New Roman',
    #                         font_size=36,
    #                         x=window.width//2, y=window.height//2,
    #                         anchor_x='center', anchor_y='center')

    # if display_mode == "bar":
    #     #objects = bar_make(db_array)
    # elif display_mode == "line":
    #     #objects = line_make(db_array)
    # else:
    #     msg = "Invalid display mode. Choose either 'bar' or 'line'"
    #     raise ValueError(msg)

    #audio.play()


#==============#
# Bar Graphing #
#==============#

# def bar_make(db_array: np.ndarray) -> list[pyglet.shapes.Rectangle]:
#     bar_width = int((WINDOW_WIDTH - (2 * EDGE_XPAD) - ((db_array.shape[1] - 1) * ITEM_SPACING)) / db_array.shape[1])
#     #To have maximum volume take up entire window:
#     #BAR_YSCALE = (WINDOW_HEIGHT - (2 * EDGE_YPAD)) / 80
#     bars = []
#     for bar_index in range(db_array.shape[1]):
#         bars.append(pyglet.shapes.Rectangle(x=EDGE_XPAD + (bar_index * ITEM_SPACING) + (bar_index * bar_width),
#                                             y=EDGE_YPAD, width=bar_width, height=1, color=ITEM_COLOR))
#     return bars


#===============#
# Line Graphing #
#===============#

# def line_make(db_array: np.ndarray) -> list[pyglet.shapes.Line]:
#     item_width = int((WINDOW_WIDTH - (2 * EDGE_XPAD) - ((db_array.shape[1] - 1) * ITEM_SPACING)) / db_array.shape[1])

#     lines = []
#     for i in range(len(db_array[1]) - 1):
#         x = EDGE_XPAD + (i * ITEM_SPACING) + (i * item_width)
#         x2 = EDGE_XPAD + ((i+1) * ITEM_SPACING) + ((i+1) * item_width)
#         lines.append(pyglet.shapes.Line(x=x, y=EDGE_YPAD, x2=x2, y2=EDGE_YPAD, width=1.0, color=ITEM_COLOR))
#     return lines


# class Updater:
#     vid_frame = 0
#     vid_total_time = 0
#     real_total_time = 0

#     @classmethod
#     def bar_update(cls, dt: int, bars: list[pyglet.shapes.Rectangle], db_array: np.ndarray) -> None:
#         time_diff = Updater.get_time_gap(dt)

#         if cls.vid_frame < db_array.shape[0]:
#             for bar_index, bar in enumerate(bars):
#                 bar.height = db_array[cls.vid_frame][bar_index] * ITEM_YSCALE
#             cls.vid_frame += 1

#         if time_diff > MAX_DELAY:
#             Updater.bar_update(0, bars, db_array)

#     @classmethod
#     def line_update(cls, dt: int, lines: list[pyglet.shapes.Line], db_array: np.ndarray) -> None:
#         time_diff = Updater.get_time_gap(dt)

#         if cls.vid_frame < db_array.shape[0]:
#             for line_index, line in enumerate(lines):
#                 line.y = db_array[cls.vid_frame][line_index] * ITEM_YSCALE
#                 line.y2 = db_array[cls.vid_frame][line_index+1] * ITEM_YSCALE
#             cls.vid_frame += 1

#             #make lines that interpolate to make smooth line

#         if time_diff > MAX_DELAY:
#             Updater.line_update(0, lines, db_array)

#     @classmethod
#     def get_time_gap(cls, dt: int) -> int:
#         cls.vid_total_time += dt
#         cls.real_total_time += (1 / FPS)
#         return cls.vid_total_time - cls.real_total_time


