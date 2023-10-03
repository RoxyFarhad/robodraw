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
from draw_wrapper import DrawWrapper
from robodraw import InternalRobot, connect, draw, draw_lines
import io
import os
import sys
import time


def getValue(minVal: float, maxVal: float) -> float:
    return float(minVal + (maxVal - minVal) * random.random())


async def main():
    logger = logging.getLogger("axidraw")
    image_path = "./puppy.jpg"
    output_contours = "./output-lines.svg"
    drawer = DrawWrapper(
        input_path=image_path, output_path=output_contours, logger=logger
    )
    robot_client = InternalRobot(
        drawer=drawer,
        logger=logger,
        api_key="3xa5lhmnugpf7xvhbjo54dfyakqjcg655wn03ze4yjfl3jga",
    )
    await robot_client.move_to_home()
    await robot_client.draw()


# start = await axidraw.get_position()

# minX, maxX, minY, maxY, z = -8, 8, -5.5, 5.5, 0
# # make sure its at the origin
# await axidraw.move_to_position([0, 0, 0], [])
# while True:
#     nextX = getValue(minX, maxX)
#     nextY = getValue(minY, maxY)
#     print(f"move to {nextX} - {nextY}")
#     _ = await axidraw.move_to_position([nextX, nextY, z], [])
# # Don't forget to close the robot when you're done!
# await robot.close()

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Parse the file to sketch on the robot")
#     parser.add_argument("--path", dest="path")
#     parser.add_argument("--output", dest="output")
#     args = parser.parse_args()

#     asyncio.run(draw(args.path, args.output))

if __name__ == "__main__":
    asyncio.run(main())
