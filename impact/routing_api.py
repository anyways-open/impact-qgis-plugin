import json

from . import transform_layer_to_WGS84, extract_valid_geometries, route_meta, lat_lon_coor, \
    fetch_non_blocking, extract_coordinates_array, staging_mode


# Initialize Qt resources from file resources.py
# Import the code for the dialog


class routing_api(object):
    default_profiles = ["car", "car.shortest", "car.opa", "car.default", "car.classifications",
                        "car.classifications_aggressive", "pedestrian", "pedestrian.shortest", "pedestrian.default",
                        "pedestrian.opa",
                        "bicycle", "bicycle.fastest", "bicycle.shortest", "bicycle.safety", "bicycle.comfort",
                        "bicycle.comfort_safety",
                        "bicycle.electrical_fastest", "bicycle.networks", "bicycle.brussels", "bicycle.genk",
                        "bicycle.antwerp",
                        "bicycle.cycle_highway", "bicycle.node_network", "bicycle.commute", "bicycle.b2w",
                        "bicycle.anyways_network"]

    def __init__(self, api_key, baseurl=None, is_impact_backend=False,
                 auth_token=None):
        
        if(baseurl == None):
            baseurl="https://routing.anyways.eu/api"
            if staging_mode:
                # baseurl = "https://staging.anyways.eu/api/routing"
                pass
        
        
        self._api_key = api_key
        self._baseurl = baseurl
        self.is_impact_backend = is_impact_backend
        self.loaded_explanations = None
        self.auth_token = auth_token

    def construct_url(self, fromCoor, toCoor, profile):
        """
        Constructs the correct URL for a 'from to'-query
        :param fromCoor: 
        :param toCoor: 
        :param profile: 
        :return: 
        """
        if self.is_impact_backend:
            return self._baseurl + "/routing?apiKey=" + self._api_key + "&profile=" + profile + "&loc=" + lat_lon_coor(
                fromCoor) + "&loc=" + lat_lon_coor(toCoor)
        return self._baseurl + "/v1/routes?apiKey=" + self._api_key + "&loc=" + fromCoor + "&loc=" + toCoor + "&profile=" + profile

    def _request_json(self, url, callback, onfail):
        fetch_non_blocking(url, lambda str: callback(json.loads(str)), onfail)

    def request_supported_profiles(self, withDescriptions):
        """
        Fetches all (public) profiles. Legacy/hidden profiles are filtered
        :return: (name or aliasname --> description, names)
        """

        def callback(raw):
            profiles = json.loads(raw)["profiles"]
            descriptions = {}
            description_keys = []
            for profile in profiles:
                type = profile["type"]  # eg "car", "bicycle", "pedestrian"
                name = profile["name"]  # eg "shortest", "fastest"
                description = profile["description"]
                descriptions[type + "." + name] = description
                if not description.lower().startswith("[legacy]"):
                    description_keys.append(type + "." + name)
                for alias in profile["aliases"]:
                    descriptions[alias] = description
            description_keys.sort()
            withDescriptions(descriptions, description_keys)

        url = self._baseurl + "/v1/profiles"
        fetch_non_blocking(url, callback, lambda err: print("Could not load profiles due to" + err))

    def request_all_routes(self, fromCoors, toCoors, profile, withRoutes, onError):
        """
        Requests a matrix call
        :param fromCoors: [number,number][], containing coordinates in "lon,lat" format
        :param toCoors:  [number,number][], containing coordinates in "lon,lat" format
        :param profile: string, the name of the profile to use
        :param: witRoutes: callback which is called with a route_meta[][] object when the call is finished
        :return: route_meta[][], where route_meta[x][y].fromCoor == fromCoors[x] and route_meta[x][y].toCoor == toCoors[y]
        """



        if self.is_impact_backend:
            url = self._baseurl + "/routing/many-to-many"
        else:
            url = self._baseurl + "/v1.1/matrix"
        
        headers = {}
        if self.auth_token is not None:
            headers = {
                "Authorization": self.auth_token
            }
            
        if not self.is_impact_backend:
            # the old api.anyways.eu/routing takes 'lat,lon'
            fromCoors = list(map(lambda c : list(reversed(c)), fromCoors))
            toCoors = list(map(lambda c : list(reversed(c)), toCoors))
        
        # More then 100 coordinates is deadly for the application - especially on slower internet - so we split them up
        
        # Result is the final result that will be sent if no toCoors are left
        # We intersperse the 'data'-list later on
        # Type: routemeta [][]
        allresults = list()
        while(len(toCoors) > 0):
            sublistTo = toCoors[0:100]
            toCoors = toCoors[100:]
            fromCoorsClone = fromCoors
            data = list()
            def callbackIntermediate(raw):
                data.extend(json.loads(raw)["routes"])
                print("Appended data")
                
            def callbackFinal(raw):
                data.extend(json.loads(raw)["routes"])
                print("Got all data, calling callback")
                # We have to fuse the 'data' list in the 'result'-list
                if len(allresults) == 0:
                    allresults.extend(data)
                else:
                    for i in range(0, len(data)):
                        allresults[i].extend(data[i])
                print("Fused lists, time to call withRoutes?", len(toCoors))
                if len(toCoors) == 0:
                    withRoutes({"routes": allresults})
    
            while(len(fromCoorsClone) > 0):
                sublist = fromCoorsClone[0:100]
                fromCoorsClone = fromCoorsClone[100:]
                postData = {
                    "profile": profile,
                    "from": sublist,
                    "to": sublistTo
                }
                
                print("Requesting routes from "+url+" with "+str(len(sublist))+" from coordinates and "+str(len(sublistTo))+" to coordinates and profile "+profile)
                print(str(len(fromCoors)) + "*" + str(len(toCoors))+" routes remaining after this batch", str(len(fromCoorsClone)) +"*"+ str(len(sublistTo)) +" routes remaining in this batch ")
    
                callback = callbackFinal if len(fromCoorsClone) == 0 else callbackIntermediate
                fetch_non_blocking(url,  callback, onError, postData=postData, headers=headers)
