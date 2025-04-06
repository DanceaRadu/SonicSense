class HelperService:
    def __init__(self):
        pass

    @staticmethod
    def getRectGridBasedOnCameraFOV():
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")