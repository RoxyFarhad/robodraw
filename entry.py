import asyncio
import logging
import random
import argparse
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.gantry import Gantry
from robodraw import connect, draw, load_image

def getValue(minVal: float, maxVal: float) -> float:
    return float(minVal + (maxVal - minVal) * random.random())

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse the file to sketch on the robot")
    parser.add_argument("--path", dest="path")
    
    args = parser.parse_args()
    
    asyncio.run(draw(args.path))


