import os
from uuid import uuid4
from django.conf import settings
from geonode.storage.manager import storage_manager


def feedback_path(filename):
    return os.path.join(settings.FEEDBACK_LOCATION, filename)


def remove_feedback(filename):
    """Delete a feedback file from storage"""
    path = feedback_path(filename)
    if storage_manager.exists(path):
        storage_manager.delete(path)


def get_unique_feedback_path(resource, filename):
    """ Generates a unique name from the given filename and
    creates a unique file upload path"""
    # create an upload path from a unique filename
    filename, ext = os.path.splitext(filename)
    unique_file_name = f'{filename}-{uuid4()}{ext}'
    upload_path = feedback_path(unique_file_name)
    return upload_path
