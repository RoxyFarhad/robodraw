from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.gantry import Gantry
from viam.components.camera import Camera, RawImage
import logging
import PIL.Image as PILImage
from PIL.Image import Image
import io
import matplotlib.pyplot as plt

from draw_wrapper import DrawWrapper
from .utils import Error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("robot")

Z_VALUE_DRAWING = 0
Z_VALUE_MOVING = 7


class InternalRobot:
    async def __init__(
        self, api_key: str, drawer: DrawWrapper, logger: logging.Logger
    ) -> None:
        self.robot = await self.connect(api_key)
        self.drawer = drawer
        self.axidraw = Gantry.from_robot(self.robot, "axidraw")
        self.logger = logger
        self.camera = Camera.from_robot(self.robot, "mac-cam")

    async def connect(self, api_key: str) -> RobotClient:
        creds = Credentials(type="robot-location-secret", payload=api_key)
        opts = RobotClient.Options(
            refresh_interval=0, dial_options=DialOptions(credentials=creds)
        )
        return await RobotClient.at_address("axidraw-main.i1zhybfo5h.viam.cloud", opts)

    async def get_and_saveimage(self, image_path):
        pic = self.camera.get_image()
        if isinstance(pic, Image):
            pic.save(image_path)
        elif isinstance(pic, RawImage):
            pic_bytes = pic.data
            image = PILImage.open(io.BytesIO(pic_bytes))
            image.save(image_path)

    async def move_to_home(self):
        curr_pos = await self.axidraw.get_position()
        await self.axidraw.move_to_position([curr_pos[0], curr_pos[1], 5], [])
        await self.axidraw.move_to_position([0, 0, 5], [])
        await self.axidraw.move_to_position([0, 0, 0], [])
        logger.info("i am home :)")

    async def move_to_next_coord(self, next_coord: tuple[float, float]):
        curr_pos = await self.axidraw.get_position()
        curr_x, curr_y = curr_pos[0], curr_pos[1]

        next_x, next_y = next_coord[0], next_coord[1]
        # move the pen upwards
        await self.axidraw.move_to_position(
            [curr_x, curr_y, Z_VALUE_MOVING], [500, 500, 1]
        )
        # move the pen in the air to the next point
        await self.axidraw.move_to_position(
            [next_x, next_y, Z_VALUE_MOVING], [500, 500, 1]
        )
        # move the pen in the air
        await self.axidraw.move_to_position(
            [next_x, next_y, Z_VALUE_DRAWING], [500, 500, 1]
        )
        return

    async def can_draw(self, x: float, y: float) -> bool:
        curr_pos = await self.axidraw.get_position()
        if len(curr_pos) < 2:
            raise Error(f"gantry returned a value with invalid coordinates: {curr_pos}")

        curr_x, curr_y = curr_pos[0], curr_pos[1]
        if curr_x == x and curr_y == y:
            return False

        return True

    async def draw_lines(self):
        contours = self.drawer.line_contors
        curr_pos = await self.axidraw.get_position()
        x, y = curr_pos[0], curr_pos[1]
        await self.axidraw.move_to_position([x, y, Z_VALUE_MOVING], [250, 250, 1])

        first_pos = contours[0][0]

        await self.axidraw.move_to_position(
            [first_pos[0], first_pos[1], Z_VALUE_MOVING], []
        )

        total_coords = 0
        for i in range(len(contours)):
            for coord in contours[i]:
                total_coords += 1

        for i in range(len(contours)):
            line = contours[i]
            for coord in line:
                x, y = coord
                if await self.can_draw(x, y):
                    _ = await self.axidraw.move_to_position(
                        [x, y, Z_VALUE_DRAWING], [250, 250, 1]
                    )
            if i == len(contours) - 1:
                # this is the last line there is
                # nothing to draw
                break
            # then you know that another exists
            # so you can move to the first point in the next line
            # you can check if you need to actually move to that position
            # becuase if you are the point that you are meant to be moving to
            # then you shouldn't move

            if len(contours[i + 1]) == 0:
                return Error(f"bad next line, cannot move in the air - {contours[i+1]}")

            next_coord = contours[i + 1][0]
            logger.info(f"moving to next cord: ${next_coord}")
            logger.info(f"at position {i} out of {total_coords}")
            await self.move_to_next_coord(next_coord)

    async def draw(self):
        try:
            logger.info(f"path: {self.drawer.output_image_path}")
            if (
                self.drawer.output_image_path is None
                or len(self.drawer.output_image_path) == 0
            ):
                raise Error("must provide a filepath to the image")

            if self.drawer is None:
                raise Error("cannot draw as there is no drawer defined for robot")

            self.drawer.load_contours()
            logger.info(f"starting to draw: {self.drawer.output_image_path}")
            await self.draw_lines()

        except Error as e:
            logger.error(msg=e.message)
