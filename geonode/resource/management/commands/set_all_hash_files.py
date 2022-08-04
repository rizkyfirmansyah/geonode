# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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

from django.core.management.base import BaseCommand
from geonode.base.models import ResourceBase
import logging

from geonode.security.utils import sha256sum


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate SHA-256 hash for every files stored in order to integrity verification or digital signatures'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore-errors',
            help='Stop after any errors are encountered.'
        )
        parser.add_argument(
            '-f',
            '--filter',
            dest='filter',
            default=None,
            help='Only update resourcebase that match the given filter'
        )
        parser.add_argument(
            '-u',
            '--username',
            dest='username',
            default=None,
            help='Only update data owned by the specified username'
        )

    def handle(self, *args, **options):
        ignore_errors = options.get('ignore_errors')
        filter = options.get('filter')
        if not options.get('username'):
            username = None
        else:
            username = options.get('username')

        all_resources = ResourceBase.objects.all().order_by('title')
        if filter:
            all_resources = all_resources.filter(title__icontains=filter)
        if username:
            all_resources = all_resources.filter(owner__username=username)

        for index, resource in enumerate(all_resources):
            logger.info(f"[{(index + 1)} / {len(all_resources)}] Checking 'title' of Resource [{resource.title}] ...")
            try:
                if not resource.hash:
                    resource.hash = sha256sum(resource.files)
                    resource.save()
            except Exception as e:
                if ignore_errors:
                    logger.error(f"[ERROR] Resource [{resource.title}] couldn't be updated")
                else:
                    raise e