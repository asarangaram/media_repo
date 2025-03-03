import os
from celery import Celery
from src.config import ConfigClass
from src.endpoint.media.media_types import MediaType
from src.media_processing.hls_streaming.hls_stream_generator import (
    HLSStreamGenerator,
    HLSVariant,
)

celery = Celery(
    "tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)  # Create a Celery instance


class CeleryTasks:
    tasks = [
        "generate_preview",
    ]  #  'generate_stream_lq',

    @classmethod
    def init_celery(cls, app):
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask
        return celery

    @celery.task(bind=True)
    def exec_generate_preview(cls, media_id):
        from src.endpoint.media.models import MediaModel

        media = MediaModel.get(media_id)
        if media:
            media_path = media.absolute_path()
            preview_path = media.preview_absolute_path_name()
            from .media_processing.create_thumbnails.image_thumbnail import (
                create_image_thumbnail,
            )
            from .media_processing.create_thumbnails.video_thumbnail import (
                create_video_thumbnail4x4,
            )

            if media.type == MediaType.VIDEO:
                create_video_thumbnail4x4(media_path, preview_path)
                return f"preview generated for {media_id}, {media.type}"
            elif media.type == MediaType.IMAGE:
                create_image_thumbnail(media_path, preview_path)
                return f"preview generated for {media_id}, {media.type}"
            else:
                return f"unsupported media type for {media_id}, {media.type}"
        return f"media not found {media_id}"

    @celery.task(bind=True)
    def exec_generate_stream_lq(cls, media_id):
        from src.endpoint.media.models import MediaModel

        media = MediaModel.get(media_id)
        if media:
            if media.type != "video":  # why MediaType.VIDEO is not working?
                return f"media_{str(media.id)}: can't stream . not a video. type: {media.type}"
            input_file = media.absolute_path()
            stream_path = os.path.join(media.content_type, f"media_{str(media.id)}")

            output_dir = os.path.join(ConfigClass.STREAM_STORAGE_LOCATION, stream_path)
            os.makedirs(os.path.dirname(output_dir), exist_ok=True)
            master_pl = os.path.join(output_dir, "adaptive.m3u8")
            if os.path.exists(master_pl):
                return f"media_{str(media.id)}: master_pl exists. not regenerating"
            generator = HLSStreamGenerator(
                input_file=input_file,
                output_dir=output_dir,
            )
            # HLSVariant(resolution=720, bitrate=900),
            # HLSVariant(resolution=480, bitrate=400),
            try:
                valid = generator.addVariants([HLSVariant(resolution=240, bitrate=200)])

            except Exception as e:
                # FIXME: WE may consider deleting if ffmpeg fails
                valid = False
            if not valid:
                return f"media_{str(media.id)}: failed to generate stream"
            return f"media_{str(media.id)}: stream generated"
        return f"media_{str(media.id)}: media not found"
