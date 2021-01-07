import requests
import sys, os.path
from urllib.parse import urljoin

BASE_URL_ANYWAYS= "https://routing.anyways.eu/"
BASE_PATH = 'api/route?'

class routing(object):

    def __init__(self, base_url=BASE_URL_ANYWAYS, url_path=BASE_PATH):
        self.url = urljoin( base_url , url_path )
        self._s = requests.Session()

    def profiles(self):
        return ["car", "car.shortest", "car.opa","car.default", "car.classifications",
        "car.classifications_aggressive", "pedestrian", "pedestrian.shortest", "pedestrian.default", "pedestrian.opa",
        "bicycle.fastest", "bicycle.shortest", "bicycle.safety", "bicycle.comfort", "bicycle.comfort_safety",
        "bicycle.electrical_fastest", "bicycle.networks", "bicycle.brussels", "bicycle.genk", "bicycle.antwerp",
        "bicycle.cycle_highway", "bicycle.node_network", "bicycle.commute",  "bicycle.b2w",  "bicycle.anyways_network"]


    def fromto(self, origin, destination, key, profile="car" ):
        """ 
        Plot a route from a origin to a destination. 

        Keyword arguments:
            origin -- the start coördinate a list in form [X,Y]
            destination -- the end coördinate in as lisr form [X,Y]
            profile -- the profile, must be from predefined list (default "car")
        """
        return self.route([origin, destination], key, profile=profile)


    def route(self, stops=[], key='' , profile="car"):
        """ 
        Plot a route with 2 or more many stops.

        Keyword arguments:
            stops -- the coördinates list in form [ [X,Y], [X,Y], ... ]
            profile -- the profile, must be from predefined list (default "car")
        """
        params = {}
        
        params["api-key"] = key
        
        if profile and not profile in self.profiles(): 
            raise Exception( "Profile most be from list: "+ ", ".join(self.profiles() ) )
        else:
            params["profile"] = profile

        if len(stops) < 2: 
           raise Exception( "Must include at least 2 stops")

        params["loc"] = [ ",".join(map(str, xy )) for xy in stops ]
        response = self._s.get(self.url, params=params)

        return response.json()