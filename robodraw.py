
import asyncio
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
import logging
import os
import sys
import argparse

from linedraw.linedraw import sketch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("robot")

class Error(Exception):
    def __init__(self, message: str) -> None:
        self.message = message  

async def load_image(filepath: str):
    
    if ".png" not in filepath and ".jpg" not in filepath and ".tif" not in filepath:
        raise Error(f"invalid image path: {filepath} - please use .jpg .tif or .png")
    
    # TODO: Support images that are not on the actual hardware
    if not os.path.exists(filepath):
        raise Error(f"filepath: {filepath} does not exist on machine")

    contours = sketch(filepath)
    print(contours) 
    
    maxX = 0
    maxY = 0

    for contor in contours:
        if len(contor) != 2:
            raise Exception("bad data -- skipping for now")
        x, y = contor[0], contor[1]
        maxX = max(maxX, maxY)


    return contours

async def connect():
    creds = Credentials(
        type='robot-location-secret',
        payload='yzl1w4e70v5c3pl44nuv9on4r7s6vaug56x3qnm32eqbqd5i')
    opts = RobotClient.Options(
        refresh_interval=0,
        dial_options=DialOptions(credentials=creds)
    )
    return await RobotClient.at_address('mbp-main.8fc0qlpm4c.viam.cloud', opts)

async def draw(
    path: str
):
    try:
        # robot = await connect()
       logger.info(f"path: {path}")
       if path is None or len(path) == 0:
           raise Error("must provide a filepath to the image")

       await load_image(path)
        
    except Error as e:
        logger.error(msg=e.message)


