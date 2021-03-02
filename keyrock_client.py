# -*- coding: utf-8 -*-

# Copyright (c) 2019 Future Internet Consulting and Development Solutions S.L.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import requests
import random
from urlparse import urlparse
from os import environ

from django.conf import settings as django_settings
from django.core.exceptions import PermissionDenied

from wstore.asset_manager.resource_plugins.plugin_error import PluginError

from settings import IDM_URL, IDM_PASSWORD, IDM_USER


class KeyrockClient(object):

    def __init__(self):
        self._login()

    def _login(self):
        body = {
            "name": IDM_USER,
            "password": IDM_PASSWORD
        }

        url = IDM_URL + '/v1/auth/tokens'
        response = requests.post(url, json=body, verify=django_settings.VERIFY_REQUESTS)

        response.raise_for_status()
        self._auth_token = response.headers['x-subject-token']

    def create_role_for_access(self, app_id, asset):
        path = '/v1/applications/{}/roles'.format(app_id)
        url = IDM_URL + path

        rnd_number = random.randint(10000, 99999)
        access_role = 'baeProduct{}Customer'.format(rnd_number)

        body = {
            "role": {
                "name": access_role
            }
        }

        resp = requests.post(url, headers={
            'X-Auth-Token': self._auth_token
        }, json=body, verify=django_settings.VERIFY_REQUESTS)

        resp.raise_for_status()
        new_role = resp.json()
        asset.meta_info['idm_role_name'] = access_role

        role_id = new_role['role']['id']
        return role_id

    def create_permission_for_access(self, app_id, idm_role_name, download_link):
        path = '/v1/applications/{}/permissions'.format(app_id)
        url = IDM_URL + path

        access_permission = 'permission_{}'.format(idm_role_name)
        parsed_url = urlparse(download_link)

        server = '{}://{}'.format(parsed_url.scheme, parsed_url.netloc)
        permission_resource = download_link.split(server, 1)[1]

        body = {
            "permission": {
                "name": access_permission,
                "description": "Access permission for BAE customers in role {}".format(idm_role_name),
                "action": "GET",
                "resource": permission_resource,
                "is_regex": False
            }
        }

        resp = requests.post(url, headers={
            'X-Auth-Token': self._auth_token
        }, json=body, verify=django_settings.VERIFY_REQUESTS)

        resp.raise_for_status()
        new_permission = resp.json()

        permission_id = new_permission['permission']['id']
        return permission_id

    def assign_permission_to_role(self, app_id, role_id, permission_id):
        path = '/v1/applications/{}/roles/{}/permissions/{}'.format(app_id, role_id, permission_id)
        url = IDM_URL + path

        body = {
            "role_permission_assignments": {
                "role_id": role_id,
                "permission_id": permission_id
            }
        }

        resp = requests.post(url, headers={
            'X-Auth-Token': self._auth_token
        }, json=body, verify=django_settings.VERIFY_REQUESTS)

        resp.raise_for_status()

    def check_role(self, app_id, idm_role_id):
        # Get available roles
        path = '/v1/applications/{}/roles/{}'.format(app_id, idm_role_id)
        roles_url = IDM_URL + path

        resp = requests.get(roles_url, headers={
            'X-Auth-Token': self._auth_token
        }, verify=django_settings.VERIFY_REQUESTS)

        if resp.status_code == 200:
            return True
        else:
            raise PluginError('The provided role is not registered in Keyrock')

    def grant_permission(self, app_id, user, idm_role_id):
        status = self.check_role(app_id, idm_role_id)

        if status:
            assign_url = IDM_URL + '/v1/applications/{}/users/{}/roles/{}'.format(app_id, user.username, idm_role_id)

            resp = requests.post(assign_url, headers={
                'X-Auth-Token': self._auth_token,
                'Content-Type': 'application/json'
            }, verify=django_settings.VERIFY_REQUESTS)

            resp.raise_for_status()

    def revoke_permission(self, app_id, user, idm_role_id):
        status = self.check_role(app_id, idm_role_id)

        if status:
            assign_url = IDM_URL + '/v1/applications/{}/users/{}/roles/{}'.format(app_id, user.username, idm_role_id)

            resp = requests.delete(assign_url, headers={
                'X-Auth-Token': self._auth_token,
                'Content-Type': 'application/json'
            }, verify=django_settings.VERIFY_REQUESTS)

            resp.raise_for_status()
