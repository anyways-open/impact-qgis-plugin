from ....clients.publish_api.Models.ProfileParametersModel import ProfileParametersModel

class ProfileModel(object):
    def __init__(self, name: str, parameters: ProfileParametersModel):
        self.name = name
        self.parameters = parameters

    @staticmethod
    def from_profile_string(profile: str) -> 'ProfileModel':
        profile_split = profile.split(".")
        if len(profile_split) <= 2:
            return ProfileModel(profile, ProfileParametersModel(0))

        percentage = int(profile_split[2][0:len(profile_split[2])-1])
        return ProfileModel(f"{profile_split[0]}.{profile_split[1]}", ProfileParametersModel(percentage))
