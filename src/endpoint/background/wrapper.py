from .models import BackgroundTaskModel

def startBackgroundProcess(id):
    BackgroundTaskModel.start(media_id=id)