from .models import BackgroundTaskModel

def startBackgroundProcess(id):
    BackgroundTaskModel.start_all(media_id=id)