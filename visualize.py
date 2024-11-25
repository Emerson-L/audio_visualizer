from __future__ import annotations
import pyglet
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.gl import *
from pyglet.math import Mat4, Vec3
import numpy as np
import random
import time
import math

#color fade based on intensity of new movement? like if a sudden thing happens it should be brighter and otherwise be fading
    #keep track of change in db wrt time, adjust brightness based on amount of change
#combine bar_update and line_update, theres a lot of duplicate lines

WINDOW_WIDTH, WINDOW_HEIGHT = 1440, 840
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
        frame_min, frame_max = get_min_max_frames(db_arr)
        print(frame_min, frame_max)
        pyglet.clock.schedule_interval(Updater.bar_update, (1 / FPS) / 1.4, objects, db_arr)
        pyglet.clock.schedule_interval(Updater.shader_update, (1 / FPS) / 1.4, frame_min, frame_max)
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
        for o in objects:
            o.draw()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        batch.draw()

    audio.play()
    pyglet.app.run()

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


def line_make(db_arr: np.ndarray) -> list[pyglet.shapes.Line]:
    line_xlen = (WINDOW_WIDTH - (2 * EDGE_XPAD)) / db_arr.shape[1]
    lines = []
    for i in range(len(db_arr[1]) - 1):
        x = EDGE_XPAD + (i * line_xlen)
        x2 = EDGE_XPAD + ((i+1) * line_xlen)
        lines.append(pyglet.shapes.Line(x=x, y=EDGE_YPAD, x2=x2, y2=EDGE_YPAD, width=2.0, color=ITEM_COLOR))

    return lines

def get_min_max_frames(db_arr: np.ndarray) -> tuple[int, int]:
    totals = []
    for i in range(db_arr.shape[0]):
        total = 0
        for j in range(db_arr.shape[1]):
            total += db_arr[i,j]
        totals.append(total)
    return min(totals), max(totals)

class Updater:
    vid_frame = 0
    vid_total_time = 0
    real_total_time = 0
    song_intensity = 0

    @classmethod
    def bar_update(cls, dt: int, bars: list[pyglet.shapes.Rectangle], db_arr: np.ndarray) -> None:
        time_diff = Updater.get_time_gap(dt)

        if cls.vid_frame < db_arr.shape[0]:
            frame_intensity = 0
            for bar_index, bar in enumerate(bars):
                bar.height = db_arr[cls.vid_frame][bar_index] * ITEM_YSCALE
                frame_intensity += db_arr[cls.vid_frame][bar_index]
            cls.vid_frame += 1
            cls.song_intensity = frame_intensity

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

    @classmethod
    def shader_update(cls, dt: float, frame_min: int, frame_max: int) -> None:
        #global drop_info
        translation_mat = Mat4.from_translation(Vec3(x=0, y=0, z=0))
        rotation_mat = Mat4.from_rotation(angle=0, vector=Vec3(0, 0, 1))
        model_mat = translation_mat @ rotation_mat
        program['model'] = model_mat

        # Pass parameters to shader
        duration = time.perf_counter() - start_time
        program['time'] = duration

        # wind_speed = 0.5 * math.sin(duration / 20)
        # print(wind_speed)
        # program['wind_speed'] = wind_speed

        # To enable storm intensity based on song intensity
        storm_intensity = cls.song_intensity / (frame_max - frame_min)
        program['storm_intensity'] = storm_intensity

#=============#
# Rain Shader #
#=============#

X_EDGE_BUFFER = 30                  #int, pixels
Y_EDGE_BUFFER = 30                  #int, pixels
MINIMUM_DROP_LENGTH = 5             #int, pixels
X_SPEED_VARIANCE_MULTIPLIER = 3.0   #float, scalar (suggest 1-5)
Y_BASE_SPEED = 600.0                #float, pixels/sec
Y_SPEED_VARIANCE_MULTIPLIER = 15.0   #float, scalar (suggest 5-25)
WIND_SPEED = 0.5                    #float, scalar (suggest 0-0.5)
MAX_SPEED_VARIANCE = 20.0           #float, pixels/sec
DEPTH_MULTIPLIER = 1.5              #float, scalar (suggest 0.5-2)
NUM_DROPS = 1000                     #int
DROP_COLOR_RGBA = (167, 177, 214, 255)

#connect music to some uniform to change rain based on music intensity or something
#Wind: two levels of noise, one slow wave for direction and one faster wave for intensity
#Can have odds of disappearing (set alpha = 0) raindrop to vary intensity

#float width = (length + minimum_drop_length) * wind_speed;
#vertical

# Vertex and fragment shader code
vertex_source = """#version 330

    layout(location = 0) in vec2 vertices;
    layout(location = 1) in vec4 colors;

    out vec4 newColor;

    uniform mat4 vp;
    uniform mat4 model;
    uniform float time;

    uniform float window_height;
    uniform float window_width;
    uniform int num_drops;
    uniform int x_edge_buffer;
    uniform int y_edge_buffer;
    uniform int minimum_drop_length;
    uniform float wind_speed;
    uniform float y_base_speed;
    uniform float y_speed_variance_multiplier;
    uniform float max_speed_variance;
    uniform float depth_multiplier;
    uniform float storm_intensity;

    void main()
    {
        int triangle_ID = int(floor(gl_VertexID / 3));
        int vertex_num = int(mod(gl_VertexID, 3));

        float unique_value = mod(triangle_ID, max_speed_variance);
        float y_speed = y_base_speed + (y_speed_variance_multiplier * unique_value);
        float x_speed = y_speed * wind_speed;
        float length = depth_multiplier * unique_value;
        float width = x_speed * (minimum_drop_length + length) / y_speed;

        float y_displace = y_speed * mod(time, ((window_height + (2 * y_edge_buffer)) / y_speed));
        float x_displace = x_speed * mod(time, ((window_width + (2 * x_edge_buffer)) / x_speed));

        float new_y = vertices.y - y_displace;
        float new_x = vertices.x - x_displace;

        if (new_y < -y_edge_buffer)
            new_y = new_y + window_height + (2 * y_edge_buffer);
        if (new_x < -x_edge_buffer)
            new_x = new_x + window_width + (2 * x_edge_buffer);
        if (new_x > window_width + x_edge_buffer)
            new_x = new_x - window_width - (2 * x_edge_buffer);
        if (vertex_num == 2)
        {
            new_y = new_y + length;
            new_x = new_x + width;
        }
        vec2 newVertex = vec2(new_x, new_y);

        gl_Position = vp * model * vec4(newVertex, 0.0f, 1.0f);
        newColor = colors;

        if (new_y < 0.0f || new_y > window_height || new_x < 0.0f || new_x > window_width)
            newColor = vec4(0.0, 0.0, 0.0, 0.0);
        if (triangle_ID < (1 - storm_intensity) * num_drops)
            newColor = vec4(0.0, 0.0, 0.0, 0.0);
    }
"""

fragment_source = """#version 330
    in vec4 newColor;
    out vec4 outColor;

    void main()
    {
        outColor = newColor;
    }
"""

batch = pyglet.graphics.Batch()
vert_shader = Shader(vertex_source, 'vertex')
frag_shader = Shader(fragment_source, 'fragment')
program = ShaderProgram(vert_shader, frag_shader)

# Making the view projection matrix
view_mat = Mat4.from_translation(Vec3(x=0, y=0, z=-1))
projection_mat = Mat4.orthogonal_projection(left=0, right=WINDOW_WIDTH, bottom=0, top=WINDOW_HEIGHT, z_near=0.1, z_far=1000)
view_projection = projection_mat @ view_mat
program['vp'] = view_projection

# Pass static parameters to shader
program['window_height'] = float(WINDOW_HEIGHT)
program['window_width'] = float(WINDOW_WIDTH)
program['num_drops'] = int(NUM_DROPS)
program['x_edge_buffer'] = int(X_EDGE_BUFFER)
program['y_edge_buffer'] = int(Y_EDGE_BUFFER)
program['minimum_drop_length'] = int(MINIMUM_DROP_LENGTH)
program['y_base_speed'] = float(Y_BASE_SPEED)
program['y_speed_variance_multiplier'] = float(Y_SPEED_VARIANCE_MULTIPLIER)
program['wind_speed'] = float(WIND_SPEED)
program['max_speed_variance'] = float(MAX_SPEED_VARIANCE)
program['depth_multiplier'] = float(DEPTH_MULTIPLIER)
program['storm_intensity'] = 1

def create_rain_mesh(num_drops: int) -> None:
    vertices = np.empty(shape=(num_drops * 6), dtype=int)
    colors = np.empty(shape=(num_drops * 12), dtype=int)

    for i in range(0, num_drops * 6, 6):
        center_point = (random.randint(-X_EDGE_BUFFER, WINDOW_WIDTH + X_EDGE_BUFFER),
                        random.randint(-Y_EDGE_BUFFER, WINDOW_HEIGHT + Y_EDGE_BUFFER))

        vertices[i]     = center_point[0] - 1  #bottom left x
        vertices[i + 1] = center_point[1]      #bottom left y
        vertices[i + 2] = center_point[0] + 1  #bottom right x
        vertices[i + 3] = center_point[1]      #bottom right y
        vertices[i + 4] = center_point[0]      #top x
        vertices[i + 5] = center_point[1] + MINIMUM_DROP_LENGTH  #top y

    for i in range(0, num_drops * 12, 12):
        for j in range(0, 12, 4):
            colors[i + j] = DROP_COLOR_RGBA[0]
            colors[i + j + 1] = DROP_COLOR_RGBA[1]
            colors[i + j + 2] = DROP_COLOR_RGBA[2]
            colors[i + j + 3] = DROP_COLOR_RGBA[3]


    program.vertex_list((num_drops * 3), gl.GL_TRIANGLES, batch=batch, vertices=('f', vertices), colors=('Bn', colors))

create_rain_mesh(NUM_DROPS)
start_time = time.perf_counter()
