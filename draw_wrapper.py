import os
from svgpathtools import svg2paths, CubicBezier, wsvg, Path, Line

from logging import Logger
from typing import List
from linedraw.linedraw import sketch
import math
from utils import Error
import numpy as np
import cmath
import matplotlib.pyplot as plt


class DrawWrapper:
    def __init__(self, input_path: str, output_path: str, logger: Logger) -> None:
        # define vars here
        self.input_image_path = input_path
        self.output_image_path = output_path
        self.line_contors: List[List[tuple[float, float]]] = []
        self.logger = logger

    def normalize_contours(
        self, contours: List[List[tuple[float, float]]],
    ):
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

        new_contours: List[List[tuple[float, float]]] = []
        diag_length = math.sqrt((maxX-minX)*(maxX-minX) + (maxY-minY)*(maxY-minY))   
        for line in contours:
            new_line = []
            for coordinate in line:
                if len(coordinate) != 2:
                    raise Error(
                        f"in creating new contours: could not normalize counters, bad coordinate: {line}"
                    )
                normalized_x = (coordinate[0] - minX) / diag_length
                normalized_y = (coordinate[1] - minY) / diag_length
                new_line.append((normalized_x, normalized_y))

            new_contours.append(new_line)

        self.line_contors = new_contours

    def load_contours(self):
        if (
            ".png" not in self.input_image_path
            and ".jpg" not in self.input_image_path
            and ".tif" not in self.input_image_path
        ):
            raise Error(
                f"invalid image path: {self.input_image_path} - please use .jpg .tif or .png"
            )

        if self.output_image_path is None:
            self.output_image_path = (
                os.path.abspath(os.getcwd()) + "/linedraw/output/out.svg"
            )

        if (
            os.path.isdir(self.output_image_path)
            or ".svg" not in self.output_image_path
        ):
            raise Error(f"invalid output file, must be file containing .svg")

        # TODO: Support images that are not on the actual hardware
        if not os.path.exists(self.input_image_path):
            raise Error(f"filepath: {self.input_image_path} does not exist on machine")

        contours = sketch(self.input_image_path, self.output_image_path)

        self.normalize_contours(contours, 5.5, 7)


class BezierDrawer:
    def __init__(self, filepath: str, logger: Logger) -> None:
        self.filepath = filepath
        self.logger = logger

    # converts a bezier curve into a list of smaller points
    def calculate_bezier_curve(self, bezier: CubicBezier) -> List[tuple[float, float]]:
        NUM_POINTS = 100
        points_on_curve: List[tuple[float, float]] = []
        for i in range(NUM_POINTS + 1):
            t = i / NUM_POINTS
            point = bezier.point(t)
            coords = cmath.polar(point)
            points_on_curve.append(coords)

        return points_on_curve

    def cubic_bezier_sample(self, start, control1, control2, end):
        inputs = np.array(
            [
                [start[0], start[1]],
                [control1[0], control1[1]],
                [control2[0], control2[1]],
                [end[0], end[1]]
            ]
        )
        cubic_bezier_matrix = np.array(
            [[-1, 3, -3, 1], [3, -6, 3, 0], [-3, 3, 0, 0], [1, 0, 0, 0]]
        )
        partial = cubic_bezier_matrix.dot(inputs)
        return lambda t: np.array([t**3, t**2, t, 1]).dot(partial)

    def convert_svg_to_paths(self) -> List[Path]:
        paths = svg2paths(self.filepath)[0]
        return paths
    
    def convert_paths_to_coordinates(self, paths: List[Path]) -> List[List[tuple[float, float]]]:
        
        all_points = []
        print(paths)
        for path in paths:
            segments = []
            # for each segnment draw the line differently 
            for line in path:
                if isinstance(line, Line):
                    start = [line.start.real, line.start.imag]
                    # start_robin = [line.start.
                    end = [line.end.real, line.end.imag]
                    # start, end = cmath.polar(line.start), cmath.polar(line.end)
                    segments.append((start, end))
            all_points.append(segments)
        return all_points
    
    async def convert_svg_to_contours(self):
        paths = svg2paths(self.filepath)[0]
        print(paths)
        # wsvg(paths, filename="./output1.svg")

        all_points = []
        for path in paths:
            for curve in path:
                bezier: CubicBezier = curve
                # points = self.calculate_bezier_curve(bezier)
                # all_points.extend(points)
                # plt.plot([p[0] for p in points], [p[1] for p in points], color='red')

                curve = self.cubic_bezier_sample(cmath.polar(bezier.start), cmath.polar(bezier.control1), cmath.polar(bezier.control2), cmath.polar(bezier.end))
                n_segments = 100
                points = np.array([curve(t) for t in np.linspace(0, 1, n_segments)])
                plt.plot(points[:, 0], points[:, 1], '-')

        plt.plot([p[0] for p in all_points], [p[1] for p in all_points], color="red")
        plt.show()
        # plt.title('Multiple Real Cubic Bézier Curves')
        # plt.legend()
        # plt.grid(True)
        # plt.show()
