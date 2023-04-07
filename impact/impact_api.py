import json
from urllib.parse import urlparse

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import Qgis, QgsMessageLog, QgsBlockingNetworkRequest

from . import fetch_non_blocking, fetch_blocking, staging_mode

BASE_URL_IMPACT_STAGING = "https://staging.anyways.eu/impact/"
BASE_URL_IMPACT =  "https://api.anyways.eu/" if not staging_mode else BASE_URL_IMPACT_STAGING
BASE_URL_IMPACT_META = "https://www.anyways.eu/impact/"  if not staging_mode else "https://staging.anyways.eu/impact/"
API_PATH = "https://api.anyways.eu/publish/" if not staging_mode else "https://staging.anyways.eu/api/publish/"
IMPACT_API_PATH = "https://api.anyways.eu/impact/" if not staging_mode else "https://staging.anyways.eu/api/impact/"
EDIT_API_PATH = "https://api.anyways.eu/edit/" if not staging_mode else "https://staging.anyways.eu/api/edit/"

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

    return parts[-1]


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
        # Cache for the available projects
        self.available_projects = None
        
        # Cache for scenarios in every project
        self.available_scenarios = dict()

        # Cache for supported profiles per token, dict {token --> string[]}
        self.supported_profiles = {}
        

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

    def routing_url_for_instance(self, branch):
        # https://github.com/anyways-open/impact-qgis-plugin/issues/29
        metaurl = EDIT_API_PATH + "branch/" + branch
        commit_id = json.loads(fetch_blocking(metaurl))["commit"]["id"]
        return API_PATH + "commit/" + commit_id

    def routing_url_for_instance_legacy(self, token, instance = ""):
        return API_PATH + token + "/" + instance

    def detect_scenarios(self, instance_name, callback):
        """
        Constructs all base URLS that are supported by this instance.
        :return: (via callback) a list of subparts where routeplanning was found + their token, e.g. [("0", "abcdef..."), ("1","qsdfqsdf"), ("2",...), ...]
        """

        if instance_name in self.available_scenarios :
            # Already cached
            callback(self.available_scenarios[instance_name])

        if self.oauth_token == None:
            # No auth-token given, use plugin call.

            def handleScenarios(scenarios):
                QgsMessageLog.logMessage("Got scenarios via legacy call:" + str(scenarios), 'ImPact Toolbox', level=Qgis.Info)
                found = []
                for scenario in scenarios:
                    name = scenario["name"]
                    if name == None or len(name) == 0:
                        name = "Scenario " + scenario["functionalName"]
                    name = name.replace("\n", " ").replace("<br>", " ").strip()
                    if "description" in scenario and scenario["description"] is not None and scenario["description"] != "":
                        name = name + " ("+scenario["description"].replace("<br>"," ").strip()+")"

                    branchId = scenario["branchId"]
                    if branchId.startswith("opa/"):
                        branchId = branchId[4:]
                    found.append((name, branchId))
                self.available_scenarios[instance_name] = found
                callback(found)

            self.__load_project(instance_name, handleScenarios, print)
            return

        def handleProjects(allProjects):
            for project in allProjects:
                project_name = project["clientId"] + "/" + project["id"]
                if project_name != instance_name:
                    continue

                self.available_scenarios[instance_name] = project["scenarioIds"]
                # Project found!
                callback(project["scenarioIds"])

        self.load_available_projects(handleProjects, print)



    def get_supported_profiles(self, instance_name, index, callback):
        def _callback(scenarios):
            scenario_path = scenarios[index]
            if(type(scenario_path) is tuple):
                scenario_path = scenario_path[1]
            self.__get_supported_profiles(scenario_path, callback)
        self.detect_scenarios(instance_name, _callback)
        
        
    def __get_supported_profiles(self, path, callback):
        """
        Fetches the supported profiles for the project from https://staging.anyways.eu/api/impact/publish/<token>/profiles
        
        If the call fails, the default list is reteruned
        
        :param index: the number of the scenario 
        :param callback: 
        :return: "type.profile"[]
        """

        if path in self.supported_profiles:
            callback(self.supported_profiles[path])
        url = API_PATH + path + "/profiles"
        
        def withData(data):
            profiles = []
            parsed = json.loads(data)["profiles"]
            for element in parsed:
                type = element["type"]
                profile = element["name"]

                if profile == "":
                    profiles.append(type)
                else:
                    profiles.append(type+"."+profile)
            self.supported_profiles[path] = profiles
            self.log("Got "+str(len(profiles))+" supported profiles from "+url)
            callback(profiles)
            
        def onError(e):
            self.log(e)
            callback(SUPPORTED_PROFILES)

        self.log("Fetching supported profiles for "+url)
        fetch_non_blocking(url, withData, onError, postData=None, headers={
            "Accept": "*/*",
        })


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
        
        This method is cached, so the network request will only be made once
        
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

    def __load_project(self, projectId, callback, onError):
        """
        Fetches the project details from an endpoint that doesn't require authentication.
        
        https://api.anyways.eu/impact/swagger/index.html#/Plugin/Plugin_GetProject
        
        :param callback: 
        :return: 
        """

        QgsMessageLog.logMessage("current project in load_project:" + projectId, 'ImPact Toolbox', level=Qgis.Info)

        def withData(response):
            if response == "":
                onError("empty result, probably invalid token")
                return
            # try:
            QgsMessageLog.logMessage("repsonse ok", 'ImPact Toolbox', level=Qgis.Info)
            project = json.loads(response)
            scenarios = project["scenarios"]
            callback(scenarios)
            # except Exception:
            #     QgsMessageLog.logMessage("failed"), 'ImPact Toolbox', level=Qgis.Info)
            #     onError("Invalid response, probably a wrong token")

        url = IMPACT_API_PATH + "plugin/project/" + projectId
        QgsMessageLog.logMessage("fetching:" + url, 'ImPact Toolbox', level=Qgis.Info)
        fetch_non_blocking(url, withData, onError, postData=None, headers={
            "Accept": "*/*",
        })
        
        
