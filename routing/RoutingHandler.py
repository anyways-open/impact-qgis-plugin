from typing import Callable

from qgis._core import QgsPointXY, QgsMessageLog, Qgis, QgsFeature, QgsApplication

from ..tools.ParsingTools import parse_float_or_default
from .tasks.RouteResult import RouteResult
from .MatrixElement import MatrixElement
from ..Result import Result
from ..layers.PointLayerHelpers import transform_layer_to_wgs84, extract_valid_geometries
from .Matrix import Matrix
from .MatrixLocation import MatrixLocation
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
        locations: list[MatrixLocation] = []
        locations_index: dict[str, int] = {}
        elements: list[MatrixElement] = []
        for line_feature in line_layer:
            line_geometry = line_feature.geometry()
            line_geometry.convertToSingleType()
            line = line_geometry.asPolyline()

            # get or create origin location.
            origin: QgsPointXY = line[0]
            origin_str = str(f"{origin.x()}-{origin.y()}")
            if origin_str in locations_index:
                origin_index = locations_index[origin_str]
            else:
                origin_index = len(locations)
                locations_index[origin_str] = len(locations)
                locations.append(MatrixLocation(origin))

            # get or create destination location.
            destination: QgsPointXY = line[len(line)-1]
            destination_str = str(f"{destination.x()}-{destination.y()}")
            if destination_str in locations_index:
                destination_index = locations_index[destination_str]
            else:
                destination_index = len(locations)
                locations_index[destination_str] = len(locations)
                locations.append(MatrixLocation(destination))

            # add forward element.
            if line_feature.fieldNameIndex("count") > -1:
                count = int(parse_float_or_default(line_feature.attribute("count"), -1))
                if count > 0:
                    elements.append(MatrixElement(origin_index, destination_index, count))

           # add backward element.
            if line_feature.fieldNameIndex("count_rev") > -1:
                count_rev = int(parse_float_or_default(line_feature.attribute("count_rev"), -1))
                if count_rev > 0:
                    elements.append(MatrixElement(destination_index, origin_index, count_rev))

        return Result(Matrix(locations, elements))

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

            if origin_geometry.geometry().isEmpty():
                QgsMessageLog.logMessage("Layer has features that empty, they are being ignored", MESSAGE_CATEGORY, Qgis.Warning)
                continue

            # QgsMessageLog.logMessage(f"{origin_geometry.geometry().asWkt()}", MESSAGE_CATEGORY, Qgis.Info)
            if isinstance(origin_geometry, QgsPointXY):
                point = origin_geometry
            else:
                point = origin_geometry.geometry().asPoint()

            count: int = 1
            if origin_geometry.fieldNameIndex("count") > -1:
                count_value = origin_geometry['count']
                if count_value is not None:
                    count = int(parse_float_or_default(count_value, 1))
            if count <= 0:
               continue

            # QgsMessageLog.logMessage(f"{point.x()}-{point.y()}", MESSAGE_CATEGORY, Qgis.Info)
            origins.append(MatrixLocation(point))
            # QgsMessageLog.logMessage(f"{count}", MESSAGE_CATEGORY, Qgis.Info)
            origin_counts.append(count)

        # build destinations list.
        destinations: list[MatrixLocation] = []
        for destination_geometry in destination_layer:
            if destination_geometry.geometry().isNull():
                QgsMessageLog.logMessage("Layer has features that are invalid", MESSAGE_CATEGORY, Qgis.Warning)
                continue

            if destination_geometry.geometry().isEmpty():
                QgsMessageLog.logMessage("Layer has features that empty, they are being ignored", MESSAGE_CATEGORY, Qgis.Warning)
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