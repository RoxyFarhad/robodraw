import asyncio
import logging
import random
import argparse
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.camera import Camera, RawImage
import PIL.Image as PILImage
from PIL.Image import Image
from viam.components.gantry import Gantry
from robodraw import connect, draw 
import io
import os
import sys

def getValue(minVal: float, maxVal: float) -> float:
    return float(minVal + (maxVal - minVal) * random.random())

async def camera_main():
    robot = await connect()
    logger = logging.getLogger("mac-camera")
    
    camera = Camera.from_robot(robot, "mac-cam")
    pic = await camera.get_image()
    image_path = "./output-image.jpg"
    output_contours = "./output-lines.svg"
    if isinstance(pic, Image):
        pic.save(image_path)
    elif isinstance(pic, RawImage):
        pic_bytes = pic.data
        image = PILImage.open(io.BytesIO(pic_bytes))
        image.save(image_path)
    
    await draw(image_path, output_contours)
    
    await robot.close()

async def main():
    robot = await connect()
    logger = logging.getLogger("axidraw")
    
    axidraw = Gantry.from_robot(robot, "axidraw")
    axis = await axidraw.get_lengths()
    start = await axidraw.get_position()
    
    minX, maxX, minY, maxY, z = -8, 8, -5.5, 5.5, 0
    # make sure its at the origin
    await axidraw.move_to_position([0, 0, 0], [])
    while True:
        nextX = getValue(minX, maxX)
        nextY = getValue(minY, maxY)
        print(f"move to {nextX} - {nextY}")
        _ = await axidraw.move_to_position([nextX, nextY, z], [])
    # Don't forget to close the robot when you're done!
    await robot.close()

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Parse the file to sketch on the robot")
#     parser.add_argument("--path", dest="path")
#     parser.add_argument("--output", dest="output")    
#     args = parser.parse_args()
    
#     asyncio.run(draw(args.path, args.output))

if __name__ == "__main__":
    asyncio.run(camera_main())
