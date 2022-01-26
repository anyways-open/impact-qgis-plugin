import json
from urllib.parse import urlparse

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import Qgis, QgsMessageLog, QgsBlockingNetworkRequest

from . import fetch_non_blocking, staging_mode

BASE_URL_IMPACT =  "https://www.anyways.eu/impact/"
BASE_URL_IMPACT_STAGING = "https://staging.anyways.eu/impact/"
BASE_URL_IMPACT_META = "https://www.anyways.eu/impact/"  if not staging_mode else "https://staging.anyways.eu/impact/"
API_PATH = "publish/"

SUPPORTED_PROFILES = ["car", "car.shortest", "car.opa", "car.default", "car.classifications",
                      "car.classifications_aggressive", "pedestrian", "pedestrian.shortest", "pedestrian.default",
                      "pedestrian.opa",
                      "bicycle", "bicycle.fastest", "bicycle.shortest", "bicycle.safety", "bicycle.comfort",
                      "bicycle.comfort_safety",
                      "bicycle.electrical_fastest", "bicycle.networks", "bicycle.brussels", "bicycle.genk",
                      "bicycle.antwerp",
                      "bicycle.cycle_highway", "bicycle.node_network", "bicycle.commute", "bicycle.b2w",
                      "bicycle.anyways_network"]


def extract_instance_name(url):
    if (not url.startswith("http")):
        return url
    path = urlparse(url).path[1:]
    parts = list(filter(lambda s: s != "", path.split("/")))
    if parts[0] == 'impact':
        del parts[0]
    try:
        int(parts[-1])
        del parts[-1]
    except:
        pass

    return "/".join(parts)


class impact_api(object):

    def __init__(self, oauth_token=None):
        """
        A small wrapper class around impact. Note that the actual routeplanning should be done with 'routing-api', however, this class helps to prepare the routing api
        :param human_url: 
        """
        if oauth_token is None:
            self.oauth_token = None
        else:
            self.oauth_token = oauth_token.strip().strip("\n")
        self.available_projects = None

    def log(self, msg):
        QgsMessageLog.logMessage(msg, 'ImPact Toolbox', level=Qgis.Info)

    def _test_url(self, url):
        request = QNetworkRequest(QUrl(url))
        # use a blocking request here
        blockingRequest = QgsBlockingNetworkRequest()
        result = blockingRequest.get(request)

        reply = blockingRequest.reply()
        error_code = reply.error()

        if error_code == 0:
            # We have a response from the server
            return True
        else:
            # We check the status code instead... Note that this is a total hack: we check for internal server error (too little arguments)
            # Then we know there is an instance there
            return reply.errorString().endswith("Internal Server Error")

    def routing_url_for_instance(self, instancename, scenario_name):
        base = BASE_URL_IMPACT
        if staging_mode:
            base = BASE_URL_IMPACT_STAGING
        return base + API_PATH + instancename + "/" + scenario_name

    def detect_instances(self, instance_name, callback):
        """
        Constructs all base URLS that are supported by this instance.
        :return: (via callback) a list of subparts where routeplanning was found, e.g. ["0", "1", "2", "3"]
        """

        if self.oauth_token == None:
            # No auth-token given, revert to old testing

            def test_scenario(scenario):
                return self._test_url(self.routing_url_for_instance(instance_name, scenario) + "/routing/many-to-many")

            found = []
            if test_scenario("0"):
                found.append("0")
            i = 1
            while i < 100:
                if test_scenario(str(i)):
                    found.append(str(i))
                else:
                    break
                i = i + 1
            callback(found)
            return

        def handleProjects(allProjects):
            for project in allProjects:
                project_name = project["clientId"] + "/" + project["id"]
                if project_name != instance_name:
                    continue

                # Project found!
                callback(project["scenarioIds"])

        self.load_available_projects(handleProjects, print)

    def get_outline(self, instance_name, with_geojson):
        """
        Constructs all base URLS that are supported by this instance.
        :return: (via callback) a list of subparts where routeplanning was found, e.g. ["0", "1", "2", "3"]
        """

        def handleProjects(allProjects):
            for project in allProjects:
                project_name = project["clientId"] + "/" + project["id"]
                if project_name != instance_name:
                    continue

                # Project found!
                with_geojson(project["area"])

        self.load_available_projects(handleProjects, print)

    def load_available_projects(self, callback, onError):
        """
        Fetches all projects available to the logged-in user.
        
        The callback will be called with a loaded json file.
        It has the format:
        
        { id: string (typically a city),
          clientId: string,
          scenarioIds: string[]
          name: string, descrition: string (user generated names and descriptions, often empty)
          area: outline of the impact instance, geojson polygon}[]
        
        :param callback: 
        :return: 
        """

        if self.available_projects is not None:
            callback(self.available_projects)
            return

        def withData(str):
            if str == "":
                onError("empty result, probably invalid token")
                return
            try:
                self.available_projects = json.loads(str)["projects"]
                callback(self.available_projects)
            except:
                onError("Invalid response, probably a wrong token")

        url = BASE_URL_IMPACT_META + "project"
        fetch_non_blocking(url, withData, onError, postData=None, headers={
            "Accept": "*/*",
            "Authorization": self.oauth_token
        })
