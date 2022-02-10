import json

import impact.fod_api
import impact.routing_api
from impact import feature_histogram, impact_api, setStandalone, routing_api

testtoken_location = "/home/pietervdvn/impact_bearer_token.txt"
testkey = "6_ZBbkdt2Qgp8yfBz651t_VDQenNBaAM"
setStandalone()


def test_routeplanning(writeFiles=False):
    routing = impact.routing_api.routing_api(testkey, "https://staging.anyways.eu/routing-api")

    def withProfiles(profiles, profile_keys):
        assert (len(profiles) > 0)

        routes = routing.request_all_routes(
            [[5.489040573818812, 50.95426526062005], [5.489040573818812, 50.95426526062005]],
            [[5.489526754837783, 50.96498330385117]],
            "bicycle.fastest", print, print)

    profiles = routing.request_supported_profiles(withProfiles)


def test_fod_api():
    f = open("testdata/brugge_bbox.geojson", "r")
    brugge_bbox = f.read()

    def withData(fod_data):
        print("Got " + str(len(fod_data["features"])) + " movement pairs")
        if len(fod_data["features"]) == 0:
            raise "No features returned from the FOD-data"

    def onError(e):
        raise e

    fod_api = impact.fod_api.fod_api()
    fod_data = fod_api.request(
        brugge_bbox,
        brugge_bbox,
        withData,
        onError,
        ["Bicycle", "Car"]
    )

def geojson(filename):
    f = open(filename, "r")
    return json.loads(f.read())

def wr(filename, contents):
    f = open(filename, "w")
    f.write(contents)
    f.close()


def test_hist_diff():
    zero = feature_histogram.feature_histogram(geojson("testdata/genk_car.short.geojson"))
    newSit = feature_histogram.feature_histogram(geojson("testdata/genk_bicycle.fastest.geojson"))

    all_zero = zero.subtract(zero)
    all_zero_counts = map(lambda f: f["properties"]["count"], all_zero.to_feature_list())
    assert (all(map(lambda c: c == 0, all_zero_counts)))

    diff = zero.subtract(newSit)

    commonPart = "5.49400112,50.95852472;5.49417819,50.95869369"
    carOnly = "5.49305675,50.95799405;5.49321772,50.95810222"
    cycleOnly = "5.49362015,50.95811236;5.49401721,50.9583794"

    assert (diff.histogram[commonPart]["properties"]["count"] == 0)
    assert (diff.histogram[carOnly]["properties"]["count"] == 1)
    assert (diff.histogram[cycleOnly]["properties"]["count"] == -1)

def test_traffic_shift():
    zero = feature_histogram.feature_histogram(geojson("testdata/wechel_bicycle.geojson"))
    newSit = feature_histogram.feature_histogram(geojson("testdata/wechel_car.geojson"))

    diff = zero.subtract(newSit)
    
    diff.natural_boundaries()
    
    pass


def test_impact():
    url = "https://www.anyways.eu/impact/labo/herentals/1/#11.19/51.1746/4.8697?o=4.8449208,51.1649384&d=4.8229508,51.1807887&layers=C"
    imp = impact.impact_api.impact_api()
    clean = impact.impact_api.extract_instance_name(url)
    print(clean)
    assert ("labo/herentals" == clean)
    clean_url = imp.routing_url_for_instance(clean, "1")
    print(clean_url)
    assert ("https://api.anyways.eu/publish/labo/herentals/1" == clean_url)


def test_profiles():
    def callback(profile_info, keys):
        assert len(keys) > 10
        assert profile_info["bicycle.safety"].startswith("A defensive route shying away from big roads")

    impact.routing_api.routing_api("").request_supported_profiles(callback)


def test_routing_matrix():
    impact_api.BASE_URL_IMPACT = "https://staging.anyways.eu/api/impact/"
    impact = impact_api.impact_api()
    routing = routing_api.routing_api(testkey, impact.routing_url_for_instance("99142096-ff71-47ee-b267-c85ab97c8dc8"), True)

    def withRoutes(routes):
        print("Got a response!")

    routes = routing.request_all_routes(
        [[4.77929 ,51.26195]], [[4.78835,51.26484]],
        "bicycle.short", withRoutes, print)


def test_impact_get_projects():
    f = open(testtoken_location, 'r')
    lines = f.readlines()
    if len(lines) > 1:
        raise Exception("Only a single line expected!")
    bearer_token = lines[0]
    print("Got bearer token")
    impact = impact_api.impact_api("", bearer_token)
    impact.load_available_projects(print, print)


def test_impact_attempt_login():
    auth_token = "CfDJ8Jd31YrxwuhChamTNAkp-y-x9a072KklVxQyddAQUmCeAMUUk95FoRzWjIx65IoHryZQXyjRuWgIBy7BRE6TEGX3n0QD6CdqCZOiJKmPaniroYd1JCc8PXFiWzOC7rTIYfDZXviMqdngDUeuM9zGYYrmNg6pbUdPJSBVzMYjiD1nela9Zdd1gjysBpVyqMFzD_VtjxU15d946MGy-leA3Ox0g5tJYUpsTfMdaWsGYqzkJVS85Ek5Y6XWDNLqyKjAPdCR0o8ZnykPwNoDws1x2rlug5_7LxCbCglGjRxKYOteH_ludBRRpuwqpfvwlz2iaqXZb2ExWl6PXeZ1YqWavjdQQXtoMTYmFm8AXIk3xdsNmuHjOy2uJRKuyJrYZiNrlFNBbRCUxNus1jpMvUGWAGeiglvkKLvaPnxNf8e5T96g0H1yPfco2twxQL9lHYZFew_0yX_D_epUwm8rsHQ3wulkQR6KzqpDRF1NSXYJMpOwmMZ-MTQJdimOPwQ704yrS9Gpqz4sWqjbp8bXAYUCyCLrVyCWhkY_wE-wzX-KHY1252zfmPGgZ-CoaTuLfKLYRxlinDIALD2noNZutfztse96e3QVEDCPii8eyRnbIMSvmf-s-cZShZWezoSoYTvYEHE6sgLmCSyRlekH0kEADKsxHgsfBWQLEeNmZw77Ic4FvZDPZr6iAao8RMu6XrQcNo6AYYoUNI4B8kj_zMAtYjlP73zK7o9h_fcuSivuepz-R2UA156UeLRovNYLvIaPaG72l4Z_x6FISVwY51-KD_ReoBMZD5QsJNUBKyVlV716z9dY7twfLPPl4tvz97tLNqiGx9IQtyFUQ0zjpOol2QGEeydUHTzH96IURPooRMiDKq8goftymL8NrDrOI4i_02iuUvFKFujpce8lvy2ujPGJtjKT3cv_fHgWSrDY3x2wqe-hTtAlRodNnmGu1LtN_APBx36T-QteWOYmMXYVEy1eJqe02oobkCBdOJboCxbm"
    impact_api_obj = impact_api.impact_api("https://staging.anyways.eu/impact")


# test_impact_attempt_login()


def test_boundaries():
    data = geojson("testdata/wechel_traffic_shift_car.classifictions_vs_car.short.geojson")
    hist = feature_histogram.feature_histogram(data)
    
    boundaries = hist.natural_boundaries()
    print(boundaries)



def test_all():
    print("Testing all")
    test_impact()
    test_boundaries()
    test_profiles()
    test_routing_matrix()
    test_routeplanning()
    test_hist_diff()
    test_fod_api()
    test_traffic_shift()
    # test_impact_get_projects()


test_all()
