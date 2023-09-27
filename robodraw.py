import cv2
from svgpathtools import svg2paths, CubicBezier, wsvg
import asyncio
import math
from os.path import isfile
from re import I
from typing import Optional, List
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.gantry import Gantry
from viam.components.camera import Camera
import logging
import os
import sys
import argparse
import numpy as np
import cmath
import matplotlib.pyplot as plt

from linedraw.linedraw import sketch
from linedraw.strokesort import visualize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("robot")

Z_VALUE_DRAWING = 0
Z_VALUE_MOVING = 4

class Error(Exception):
    def __init__(self, message: str) -> None:
        self.message = message  

def normalize_contours(contours: List[List[tuple[float, float]]], rangeX, rangeY) -> List[List[tuple[float, float]]]:

    maxX = -math.inf
    maxY = -math.inf
    minX = math.inf
    minY = math.inf
    for line in contours:
        for coordinate in line:

            if len(coordinate) != 2:
                raise Error(f"could not normalize counters, bad coordinate: {line}")
            
            x, y = coordinate
            maxX = max(maxX, x)
            maxY = max(maxY, y)
            minX = min(minX, x)
            minY = min(minY, y)

    """ 
    length of diagonal=sqrt((maxX-minX)*(maxX-minX)+(maxY-minY)*(maxY-minY)+(maxZ-minZ)*(maxZ-minZ))
    normalized X = (originalX - minX)/(length of diagonal) 
    normalized Y = (originalY - minY)/(length of diagonal)
    normalized Z = (originalZ - minZ)/(length of diagonal)
    """

    diagonal = math.sqrt((maxX - minX)*(maxX - minX)+(maxY-minY)*(maxY-minY))
    
    new_contours: List[List[tuple[float, float]]] = []
    for line in contours:
        new_line = []
        for coordinate in line:
            if len(coordinate) != 2:
                raise Error(f"in creating new contours: could not normalize counters, bad coordinate: {line}")
            normalized_x = (rangeY-rangeX)*((coordinate[0]-minX)/(maxX - minX)) + rangeX
            normalized_y = (rangeY-rangeX)*((coordinate[1]-minY)/(maxY - minY)) + rangeX
#            normalized_x = (coordinate[0] - minX)/(diagonal)
#            normalized_y = (coordinate[1] - minY)/(diagonal)
            new_line.append((normalized_x, normalized_y))
        
        new_contours.append(new_line)
   
    return new_contours

async def load_contours(filepath: str, output: Optional[str]):
    
    if ".png" not in filepath and ".jpg" not in filepath and ".tif" not in filepath:
        raise Error(f"invalid image path: {filepath} - please use .jpg .tif or .png")
   
    if output is None:
        output = os.path.abspath(os.getcwd()) + "/linedraw/output/out.svg" 
    
    if os.path.isdir(output) or ".svg" not in output:
        raise Error(f"invalid output file, must be file containing .svg")

    # TODO: Support images that are not on the actual hardware
    if not os.path.exists(filepath):
        raise Error(f"filepath: {filepath} does not exist on machine")

    contours = sketch(filepath, output)
    
    normalized_contours = normalize_contours(contours, -1, 1)
        
    return normalized_contours

async def connect():
    ## AXIDRAW
    # creds = Credentials(
    #     type='robot-location-secret',
    #     payload='yzl1w4e70v5c3pl44nuv9on4r7s6vaug56x3qnm32eqbqd5i')
    # opts = RobotClient.Options(
    #     refresh_interval=0,
    #     dial_options=DialOptions(credentials=creds)
    # )
    # return await RobotClient.at_address('mbp-main.8fc0qlpm4c.viam.cloud', opts)
    
    ## ROXY CAMERA
    creds = Credentials(
        type='robot-location-secret',
        payload='3xa5lhmnugpf7xvhbjo54dfyakqjcg655wn03ze4yjfl3jga')
    opts = RobotClient.Options(
        refresh_interval=0,
        dial_options=DialOptions(credentials=creds)
    )
    return await RobotClient.at_address('axidraw-main.i1zhybfo5h.viam.cloud', opts)

async def move_to_next_coord(axidraw: Gantry, next_coord: tuple[float, float]):
        
    curr_pos = await axidraw.get_position()
    curr_x, curr_y = curr_pos[0], curr_pos[1]
    
    next_x, next_y = next_coord[0], next_coord[1]
    # move the pen upwards
    await axidraw.move_to_position([curr_x, curr_y, Z_VALUE_MOVING], [])
    # move the pen in the air to the next point 
    await axidraw.move_to_position([next_x, next_y, Z_VALUE_DRAWING], [])
    return 

async def can_draw(axidraw: Gantry, x: float, y: float) -> bool:
    
    curr_pos = await axidraw.get_position()
    if len(curr_pos) < 2:
        raise Error(f"gantry returned a value with invalid coordinates: {curr_pos}")

    curr_x, curr_y = curr_pos[0], curr_pos[1]
    if curr_x == x and curr_y == y:
        return False

    return True 

# converts a bezier curve into a list of smaller points
def calculate_bezier_curve(bezier: CubicBezier) -> List[tuple[float, float]]:
    NUM_POINTS = 100
    points_on_curve: List[tuple[float, float]] = []
    for i in range(NUM_POINTS + 1):
        t = i / NUM_POINTS
        point = bezier.point(t)
        coords = cmath.polar(point)
        points_on_curve.append(coords)
    
    return points_on_curve
    
def cubic_bezier_sample(start, control1, control2, end):
    inputs = np.array([[start[0], start[1]], [control1[0], control1[1]], [control2[0], control2[1]], [control2[0], control2[1]]])
    cubic_bezier_matrix = np.array([
        [-1,  3, -3,  1],
        [ 3, -6,  3,  0],
        [-3,  3,  0,  0],
        [ 1,  0,  0,  0]
    ])
    partial = cubic_bezier_matrix.dot(inputs)
    return (lambda t: np.array([t**3, t**2, t, 1]).dot(partial))

# == control points ==
# start = np.array([0, 0])
# control1 = np.array([60, 5])
# control2 = np.array([40, 95])
# end = np.array([100, 100])
# # number of segments to generate
# n_segments = 100
# # get curve segment generator
# curve = cubic_bezier_sample(start, control1, control2, end)
# # get points on curve
# points = np.array([curve(t) for t in np.linspace(0, 1, n_segments)])
    
async def convert_svg_to_contours(filepath: str):
    
    paths, _ = svg2paths(filepath)
    wsvg(paths, filename="./output1.svg")
    
    all_points = []
    for path in paths:
        for curve in path:
            bezier: CubicBezier = curve
            points = calculate_bezier_curve(bezier)
            all_points.extend(points)
            # plt.plot([p[0] for p in points], [p[1] for p in points], color='red')
            
            # curve = cubic_bezier_sample(cmath.polar(bezier.start), cmath.polar(bezier.control1), cmath.polar(bezier.control2), cmath.polar(bezier.end))
            # n_segments = 100
            # points = np.array([curve(t) for t in np.linspace(0, 1, n_segments)])
            # plt.plot(points[:, 0], points[:, 1], '-')
    
    plt.plot([p[0] for p in all_points], [p[1] for p in all_points], color='red')
    plt.show()
    # plt.title('Multiple Real Cubic Bézier Curves')
    # plt.legend()
    # plt.grid(True)
    # plt.show()  
            
async def draw_lines(
        axidraw: Gantry, 
        contours: List[List[tuple[float, float]]]
):
    for i in range(len(contours)):
        line = contours[i]
        for coord in line:
            x, y = coord
            if can_draw(axidraw, x, y):
                _ = await axidraw.move_to_position([x,y, Z_VALUE_DRAWING], []) 
        if i == len(contours) - 1:
            # this is the last line there is 
            # nothing to draw
            break
        # then you know that another exists 
        # so you can move to the first point in the next line 
        # you can check if you need to actually move to that position 
        # becuase if you are the point that you are meant to be moving to
        # then you shouldn't move
        
        if len(contours[i+1]) == 0:
            return Error(f"bad next line, cannot move in the air - {contours[i+1]}")

        next_coord = contours[i+1][0]
        await move_to_next_coord(axidraw, next_coord)
        
async def draw(
    path: str,
    output: Optional[str]
):
    try:
        # robot = await connect()
        logger.info(f"path: {path}")
        if path is None or len(path) == 0:
           raise Error("must provide a filepath to the image")

        contours = await load_contours(path, output)
        
        # axidraw = Gantry.from_robot(robot, "axidraw")
        # draw_lines(axidraw, contours)
        
    #    await convert_svg_to_contours(path)

       # based on the svg -> image code
       # the way this works is by drawing the list of lines 
       # from coordinate to coordinate, and then between lines jump 
       # and move to the next coordinate in the same space without drawing

    except Error as e:
        logger.error(msg=e.message)


