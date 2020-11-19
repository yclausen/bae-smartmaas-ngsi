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

import base64
import requests
from urlparse import urljoin

from wstore.asset_manager.resource_plugins.plugin_error import PluginError

from settings import TENANT_MANAGER_URL, IDM_URL, IDM_PASSWORD, IDM_USER, CLIENT_ID, CLIENT_SECRET


class TenantManagerClient(object):

    def __init__(self):
        self._get_token()

    def _get_token(self):
        token_service_endpoint = '/oauth2/password'
        url = urljoin(IDM_URL, token_service_endpoint)

        params = {
            'grant_type': 'password',
            'username': IDM_USER,
            'password': IDM_PASSWORD
        }

        credentials = base64.b64encode('{}:{}'.format(CLIENT_ID, CLIENT_SECRET))
        resp = requests.post(url, data=params, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + credentials
        })

        if resp.status_code != 200:
            raise PluginError('It was not possible to generate a valid access token')

        self._auth_token = resp.json()['access_token']

    def get_tenant(self, tenant_id):
        url = TENANT_MANAGER_URL + '/tenant-manager/tenant/{}'.format(tenant_id)
        resp = requests.get(url, headers={
            'Authorization': 'Bearer ' + self._auth_token
        })
        result = resp.json()

        if resp.status_code != 200:
            raise PluginError('An error happened accessing to the tenant')

        return result

    def get_username(self, user_id):
        username = ''
        url = TENANT_MANAGER_URL + '/tenant-manager/user/'
        resp = requests.get(url, headers={
            'Authorization': 'Bearer ' + self._auth_token
        })

        if resp.status_code != 200:
            raise PluginError('Error reading user information from tenant manager')

        for user in resp.json()['users']:
            if user['id'] == user_id:
                username = user['username']
                break
        else:
            raise PluginError('User not found in tenant manager')

        return username

    def check_seller_assigned_to_tenant(self, user, tenant_id):
        assigned_to_tenant = False
        tenant = self.get_tenant(tenant_id)
        for tenant_user in tenant['users']:
            if tenant_user['name'] == user.name:
                assigned_to_tenant = True
                break

        return assigned_to_tenant

    def check_organisation_assigned_to_tenant(self, user, tenant_id):
        assigned_to_tenant = False
        tenant = self.get_tenant(tenant_id)
        if tenant['tenant_organization'] == user.name:
            assigned_to_tenant = True

        return assigned_to_tenant

    def grant_permission(self, tenant_id, tenant_info, customer, organisation):
        # organisation.name is a ID
        # customer.name is a ID
        found = len([user for user in tenant_info['users'] if user['id'] == organisation.name]) > 0

        if not found:
            patch = [
                {'op': 'add', 'path': '/users/-', 'value': {
                    'id': customer.name, 'name': self.get_username(customer.username), 'roles': ["data-consumer"]}},
            ]

            url = TENANT_MANAGER_URL + '/tenant-manager/tenant/{}'.format(tenant_id)

            resp = requests.patch(url, json=patch, headers={
                'Authorization': 'Bearer ' + self._auth_token
            })

            if resp.status_code != 200:
                raise PluginError('An error happened updating tenant')


