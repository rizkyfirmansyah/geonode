
from .utils import feedback_path
from .models import Feedback
from geonode.storage.manager import storage_manager
from celery.utils.log import get_task_logger
from geonode.celery_app import app

logger = get_task_logger(__name__)


@app.task(
    bind=True,
    name='geonode.sdi.tasks.create_feedback',
    queue='geonode',
    expires=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def create_feedback(self, object_id):
    """
    Save feedback file
    """
    logger.debug(f"Saving feedback file for #{object_id}.")

    try:
        feedback = Feedback.objects.get(id=object_id)
    except Feedback.DoesNotExist:
        logger.error(f"Feedback #{object_id} does not exist.")
        raise

    image_file = None

    f_name = feedback_path(feedback.feedback_file.name)
    print(f_name)
    if storage_manager.exists(f_name):
        image_file = storage_manager.open(f_name, 'rb')

    if image_file is not None:
        image_file.close()

    logger.debug(f"Saving feedback #{object_id} created.")