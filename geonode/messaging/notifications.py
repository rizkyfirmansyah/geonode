#########################################################################
#
# Copyright (C) 2020 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import logging

from django.conf import settings
from user_messages.models import Message
from user_messages.signals import message_sent

from geonode.notifications_helper import send_notification

logger = logging.getLogger(__name__)


def message_received_notification(**kwargs):
    """ Send a notification when a comment to a layer, map or document has
    been submitted
    """
    notice_type_label = 'message_received'
    message = kwargs.get('message')
    thread = message.thread

    recipients = _get_user_to_notify(message)

    ctx = {
        'message': message.content,
        'thread_subject': thread.subject,
        'sender': message.sender,
        'thread_url': settings.SITEURL + thread.get_absolute_url()[1:],
        'site_url': settings.SITEURL
    }
    logger.debug(f"message_received_notification to: {recipients}")
    send_notification(recipients, notice_type_label, ctx)


def _get_user_to_notify(message):
    thread = message.thread
    users = thread.single_users.all() | thread.group_users.all()
    return users.exclude(username=message.sender.username).distinct()


def initialize_notification_signal():
    message_sent.connect(
        message_received_notification,
        sender=Message
    )


def send_inbox(request, subject, content, send_to):
      
      # thread = Thread.objects.create(subject=subject)
      # thread.userthread_set.create(user=send_to, unread=True)
      # thread.userthread_set.create(user=request.user, unread=False)
      # Message.objects.create(
      #     sender=request.user,
      #     thread=thread,
      #     content=content
      # )
      Message.objects.new_message(
          from_user=request.user,
          to_users=[send_to],
          subject=subject,
          content=content
      )

      logger.debug(f"sending inbox to: {send_to} from: {request.user}")

      return Message