import copy

from . import route_meta

class feature_histogram(object):
    """"
    A feature histogram consist of a single dict, which contains some linestring-features indexed over the GUID
    These features contain a property 'frequency' that contains the number of occurences
    
    Note that if a feature contains the property 'count', this count is used instead of 1
    """

    def __init__(self, features):
        self.histogram = {}
        self.add_features(features)

    def add_feature(self, feature):
        if feature == None:
            return

        if isinstance(feature, route_meta.route_meta):
            self.add_features(feature.features)
            return

        hist = self.histogram
        if feature["geometry"]["type"] == "Point":
            return

        key = feature["properties"]["guid"]
        count = 1
        if 'count' in feature["properties"]:
            count = feature["properties"]["count"]
        if count == NULL:
            count = 0
        if key in hist:
            hist[key]["properties"]["count"] += count
        else:
            feature["properties"]["count"] = count
            hist[key] = feature

    def add_features(self, features):
        if not isinstance(features, list) and features["type"] == "FeatureCollection":
            features = features["features"]

        for feature in features:
            self.add_feature(feature)

    def to_feature_list(self):
        return list(self.histogram.values())

    def to_geojson(self):
        return {
            "type": 'FeatureCollection',
            "features": self.to_feature_list()
        }

    def log(self, msg):
        # QgsMessageLog.logMessage(msg, 'ImPact Toolbox', level=Qgis.Info)
        pass


    def natural_boundaries(self, bin_count_target = 4):
        """
        Creates a range of boundaries to give a natural impression of the counts
        :return: 
        """

        def standard_deviation(ls):
            n = len(ls)
            if n == 0:
                return 0
            mean = sum(ls) / n
            var = sum((x - mean)**2 for x in ls) / n
            std_dev = var ** 0.5
            return std_dev




        all_counts_abs = []
        for key in self.histogram:
            all_counts_abs.append(abs(self.histogram[key]["properties"]["count"]))
        
        if bin_count_target > len(all_counts_abs):
            # There are more target bins then actual features: we tone done the expectation here
            bin_count_target = len(all_counts_abs)
        
        count_hist = {}
        for c in all_counts_abs:
            if c in count_hist:
                count_hist[c] = count_hist[c] + 1
            else:
                count_hist[c] = c
        
        
        if 0 in count_hist:
            del count_hist[0] # We don't care about the entries if there is no traffic shift
        
        # Lets create bins: we start with one big bin and try to split it up
        # A bin is a tuple with a min-value (inclusive) and a max-value (exclusive)
        current_bins = [ (1, max(all_counts_abs) + 1) ]
        
        
        def std_dev_for_bin(ranges):
            items = []
            for key in range(ranges[0], ranges[1]):
                if key in count_hist:
                    items.append(count_hist[key])
            return standard_deviation(items)

        def std_dev_for_bin_at(i):
            return std_dev_for_bin(current_bins[i]) 
        
        # Next, we split the range with the biggest deviation
        while len(current_bins) < bin_count_target:
            highest_std_dev = None
            highest_std_dev_index = None
            for i in range(len(current_bins)):
                (range_start, range_end) = current_bins[i]
                if range_start + 1 >= range_end:
                    # A bin consisting of only one element can't be split, so we skip this iteration
                    continue
                std_dev = std_dev_for_bin_at(i)
                if highest_std_dev is None or highest_std_dev < std_dev:
                    highest_std_dev_index = i
                    highest_std_dev = std_dev
                
            if highest_std_dev_index is None:
                # Not a single bin can be split anymore, so we are done
                return current_bins
                    
            # We split bin 'highest_std_dev_index' at a point which minimizes the std_dev of both sub-bins
            (range_start, range_end) = current_bins[highest_std_dev_index]
            dev_diff = None
            chosen_split_point = None
            for splitpoint in range(range_start + 1, range_end):
                std_dev_left = std_dev_for_bin((range_start, splitpoint))
                std_dev_right = std_dev_for_bin((splitpoint, range_end))
                diff = abs(std_dev_left - std_dev_right)
                if(dev_diff is None or diff < dev_diff):
                    # We found a better split
                    chosen_split_point = splitpoint
                    dev_diff = diff
            # pop does remove the item
            current_bins.pop(highest_std_dev_index)
            current_bins.insert(highest_std_dev_index, (range_start, chosen_split_point))
            current_bins.insert(highest_std_dev_index + 1, (chosen_split_point, range_end))
                
        return current_bins 

    def subtract(self, other):
        new_hist = feature_histogram([])

        common_guids = set()
        for guid in self.histogram:
            if guid not in other.histogram:
                self.log("Added " + guid + " which only occurs in self")
                new_hist.histogram[guid] = copy.deepcopy(self.histogram[guid])
            else:
                common_guids.add(guid)

        for guid in other.histogram:

            other_f = other.histogram[guid]
            if guid not in self.histogram:
                # We copy over this previously unseen feature
                other_f = copy.deepcopy(other.histogram[guid])
                other_f["properties"]["count"] = -other_f["properties"]["count"]
                new_hist.histogram[guid] = other_f
                self.log("Added " + guid + " which only occurs in other")
            else:
                common_guids.add(guid)

        for guid in common_guids:
            zero_f = self.histogram[guid]
            other_f = other.histogram[guid]
            zero_count = zero_f["properties"]["count"]
            other_count = other_f["properties"]["count"]

            copied = copy.deepcopy(zero_f)
            copied["properties"]["count"] = zero_count - other_count
            self.log("Added " + guid + " which only occurs in both, count is " + str(zero_count - other_count))

            new_hist.histogram[guid] = copied

        return new_hist
