import pyglet
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet import gl
from pyglet.math import Mat4, Vec3
import random
import numpy as np
import time

#Fix ciruclar import problem
#from visualize import WINDOW_HEIGHT, WINDOW_WIDTH
WINDOW_WIDTH, WINDOW_HEIGHT = 1400, 540

X_DIRECTION = 1                     #int, 1=left, -1=right
X_EDGE_BUFFER = 30                  #int, pixels
X_BASE_SPEED = 15.0                 #float, pixels/sec
X_MAX_SPEED_VARIANCE = 10.0         #float, pixels/sec
X_SPEED_VARIANCE_MULTIPLIER = 1.0   #float, scalar (suggest 0-3)
Y_EDGE_BUFFER = 30                  #int, pixels
Y_BASE_SPEED = 150.0                #float, pixels/sec
Y_MAX_SPEED_VARIANCE = 30.0         #float, pixels/sec
Y_SPEED_VARIANCE_MULTIPLIER = 15.0  #float, scalar (suggest 10-25)
DEPTH_MULTIPLIER = 1.5              #float, scalar (suggest 0.5-2)

# Vertex and fragment shader code

#CURRENT CLUNKY SOLUTION: changing color to background color rather than changing alpha
    #because glEnable doesn't work and alpha doesn't work
# newColor = vec4(26.0/255, 40.0/255, 86.0/255, 0.0);
# newColor = vec4(0.0, 0.0, 0.0, 0.0);

vertex_source = """#version 330

    layout(location = 0) in vec2 vertices;
    layout(location = 1) in vec4 colors;

    out vec4 newColor;

    uniform mat4 vp;
    uniform mat4 model;
    uniform float time;

    uniform float window_height;
    uniform float window_width;
    uniform int x_direction;
    uniform float x_edge_buffer;
    uniform float x_base_speed;
    uniform float x_max_speed_variance;
    uniform float x_speed_variance_multiplier;
    uniform float y_edge_buffer;
    uniform float y_base_speed;
    uniform float y_max_speed_variance;
    uniform float y_speed_variance_multiplier;
    uniform float depth_multiplier;

    void main()
    {
        int triangle_ID = int(floor(gl_VertexID / 3));
        int vertex_num = int(mod(gl_VertexID, 3));

        float y_speed = y_base_speed + y_speed_variance_multiplier * mod(triangle_ID, y_max_speed_variance);
        float x_speed = x_base_speed + x_speed_variance_multiplier * mod(triangle_ID, x_max_speed_variance);
        float y_scale = depth_multiplier * mod(triangle_ID, y_max_speed_variance);

        float y_displace = y_speed * mod(time, ((window_height + (2 * y_edge_buffer)) / y_speed));
        float x_displace = x_direction * x_speed * mod(time, ((window_width + (2 * x_edge_buffer)) / x_speed));

        float new_y = vertices.y - y_displace;
        float new_x = vertices.x - x_displace;

        if (new_y < -y_edge_buffer)
            new_y = new_y + window_height + (2 * y_edge_buffer);
        if (vertex_num == 2)
            new_y = new_y + y_scale;
        if (new_x < -x_edge_buffer)
            new_x = new_x + window_width + (2 * x_edge_buffer);
        if (new_x > window_width + x_edge_buffer)
            new_x = new_x - window_width - (2 * x_edge_buffer);
        vec2 newVertex = vec2(new_x, new_y);

        gl_Position = vp * model * vec4(newVertex, 0.0f, 1.0f);
        newColor = colors;

        if (new_y < 0.0f || new_y > window_height || new_x < 0.0f || new_x > window_width)
            newColor = vec4(26.0/255, 40.0/255, 86.0/255, 0.0);

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

#Passing parameters to shader
program['window_height'] = float(WINDOW_HEIGHT)
program['window_width'] = float(WINDOW_WIDTH)
program['x_direction'] = X_DIRECTION
program['x_edge_buffer'] = float(X_EDGE_BUFFER)
program['x_base_speed'] = X_BASE_SPEED
program['x_max_speed_variance'] = X_MAX_SPEED_VARIANCE
program['x_speed_variance_multiplier'] = X_SPEED_VARIANCE_MULTIPLIER
program['y_edge_buffer'] = float(Y_EDGE_BUFFER)
program['y_base_speed'] = Y_BASE_SPEED
program['y_max_speed_variance'] = Y_MAX_SPEED_VARIANCE
program['y_speed_variance_multiplier'] = Y_SPEED_VARIANCE_MULTIPLIER
program['depth_multiplier'] = DEPTH_MULTIPLIER

drop_color_rgba = (167, 177, 214, 255)

#Wind: two levels of noise, one slow wave for direction and one faster wave for intensity
#Rain intesnity: one very slow and low amplitude wave
    #but ideally get info from song

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
        vertices[i + 5] = center_point[1] + 2  #top y

    for i in range(0, num_drops * 12, 12):
        for j in range(0, 12, 4):
            colors[i + j] = drop_color_rgba[0]
            colors[i + j + 1] = drop_color_rgba[1]
            colors[i + j + 2] = drop_color_rgba[2]
            colors[i + j + 3] = drop_color_rgba[3]

    program.vertex_list((num_drops * 3), gl.GL_TRIANGLES, batch=batch, vertices=('f', vertices), colors=('Bn', colors))

create_rain_mesh(500)

start_time = time.perf_counter()

#1:29:30 in vid
def shader_update(dt: float) -> None:
    #global drop_info
    translation_mat = Mat4.from_translation(Vec3(x=0, y=0, z=0))
    rotation_mat = Mat4.from_rotation(angle=0, vector=Vec3(0, 0, 1))
    model_mat = translation_mat @ rotation_mat
    program['model'] = model_mat

    duration = time.perf_counter() - start_time
    program['time'] = duration




