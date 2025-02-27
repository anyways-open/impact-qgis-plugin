from typing import Callable

from qgis._core import QgsPointXY, QgsMessageLog, Qgis, QgsFeature, QgsApplication

from .tasks.RouteResult import RouteResult
from .MatrixElement import MatrixElement
from ..Result import Result
from ..layers.PointLayerHelpers import transform_layer_to_wgs84, extract_valid_geometries
from .Matrix import Matrix
from .MatrixLocation import MatrixLocation
from .MatrixOriginLocation import MatrixOriginLocation
from .RoutingNetwork import RoutingNetwork
from .tasks.RoutingTask import RoutingTask
from .tasks.RoutingTaskSettings import RoutingTaskSettings
from ..settings import MESSAGE_CATEGORY

class RoutingHandler(object):
    def __init__(self):
        pass

    @staticmethod
    def start_route_planning(task_name: str, network: RoutingNetwork, profile: str, matrix: Matrix, callback: Callable[[list[RouteResult]], None]) -> None:
        routing_task = RoutingTask(RoutingTaskSettings(name=task_name, network=network, profile=profile, matrix=matrix, callback=callback))
        RoutingTask.RUNNING_TASKS.append(routing_task)
        QgsApplication.taskManager().addTask(RoutingTask.RUNNING_TASKS[len(RoutingTask.RUNNING_TASKS)-1])

    @staticmethod
    def build_matrix_from_lines(line_layer) -> Result[Matrix]:
        line_layer = transform_layer_to_wgs84(line_layer)

        # build origins and destinations
        origins: list[MatrixOriginLocation] = []
        destinations: list[MatrixLocation] = []
        for line_feature in line_layer:
            line_geometry = line_feature.geometry()
            line_geometry.convertToSingleType()
            line = line_geometry.asPolyline()

            # do forward.
            count = int(float(line_feature.attribute('count')))
            if count > 0:
                origins.append(MatrixOriginLocation(line[0], count))
                destinations.append(MatrixLocation(line[line(line)-1]))

            # do backward.
            count_rev = int(float(line_feature.attribute('count_rev')))
            if count_rev > 0:
                origins.append(MatrixOriginLocation(line[line(line) - 1], count_rev))
                destinations.append(MatrixLocation(line[0]))

        return Result(Matrix(origins, destinations))

    @staticmethod
    def build_matrix_from_points(origin_layer, destination_layer) -> Result[Matrix]:
        # make sure things are wgs84 and geometries are valid
        origin_layer = transform_layer_to_wgs84(origin_layer)
        destination_layer = transform_layer_to_wgs84(destination_layer)

        # build origins list.
        origins: list[MatrixLocation] = []
        origin_counts: list[int] = []
        for origin_geometry in origin_layer:
            if origin_geometry.geometry().isNull():
                QgsMessageLog.logMessage("Layer has features that are invalid", MESSAGE_CATEGORY, Qgis.Warning)
                continue

            if isinstance(origin_geometry, QgsPointXY):
                point = origin_geometry
            else:
                point = origin_geometry.geometry().asPoint()

            count: int = 1
            if origin_geometry.fieldNameIndex("count") > -1:
                count_value = origin_geometry['count']
                if count_value is not None:
                    count = int(float(count_value))
            if count <= 0:
               continue

            origins.append(MatrixLocation(point))
            origin_counts.append(count)

        # build destinations list.
        destinations: list[MatrixLocation] = []
        for destination_geometry in destination_layer:
            if destination_geometry.geometry().isNull():
                QgsMessageLog.logMessage("Layer has features that are invalid", MESSAGE_CATEGORY, Qgis.Warning)
                continue

            if isinstance(destination_geometry, QgsPointXY):
                point = destination_geometry
            else:
                point = destination_geometry.geometry().asPoint()

            destinations.append(MatrixLocation(point))

        # build locations list.
        locations: list[MatrixLocation] = []
        locations.extend(origins)
        locations.extend(destinations)

        # build elements.
        elements: list[MatrixElement] = []
        origin_count = len(origins)
        for o, origin in enumerate(origins):
            for d, destination in enumerate(destinations):
                elements.append(MatrixElement(o, d + origin_count, origin_counts[o]))

        return Result(Matrix(locations, elements))
