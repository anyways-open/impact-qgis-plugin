from qgis.core import *

staging_mode = False


def generate_layer_report(features):
    """
    Creates a small piece of text giving some details about the (properties of) the features
    :param features: a list of Line-features
    """

    has_count = 0
    has_count_rev = 0
    count_is_null = 0
    count_is_zero = 0
    total_count = 0
    total_count_rev = 0
    for f in features:
        try:
            c = f["count"]
            if c == NULL:
                count_is_null += 1
            elif c == 0:
                count_is_zero += 1
            else:
                total_count += c
                has_count += 1
        except:
            pass

        try:
            rc = f["count_rev"]
            if rc == NULL:
                pass
            elif rc == 0:
                pass
            else:
                total_count_rev += rc
                has_count_rev += 1
        except:
            pass

    if (has_count + has_count_rev) == 0:
        return "No trips have a field 'count' set. Nothing will be routeplanned. Select a different layer or add the appropriate values."

    total_str = "This layer contains " + str(len(features)) + " trips."
    forward_count_str = str(has_count) + " trips have a count set for a total of " + str(
        total_count) + " vehicles."

    has_null_str = ""
    if count_is_null > 0:
        has_null_str = "\n" + str(
            count_is_null) + " trips have NULL as count. They will be routeplanned, but their count will be interpreted as 0."

    return "\n".join([total_str, forward_count_str + has_null_str])
