# -*- coding: utf-8 -*-

# Copyright (c) 2020 Future Internet Consulting and Development Solutions S.L.

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

from wstore.asset_manager.resource_plugins.plugin import Plugin
from wstore.asset_manager.resource_plugins.plugin_error import PluginError
from wstore.models import User

from keyrock_client import KeyrockClient
from tenant_manager_client import TenantManagerClient
from settings import UNITS, CLIENT_ID, CLIENT_SECRET, MARKET_CLIENT_ID

# To make the media_type accessible for further access
header_type = []


class SmartMaasNGSIQuery(Plugin):

    def __init__(self, plugin_model):
        super(SmartMaasNGSIQuery, self).__init__(plugin_model)
        self._units = UNITS

    # Before validating the product spec contents and saving the asset info in the database
    def on_pre_product_spec_validation(self, provider, asset_t, media_type, url):
        header_type.append(media_type)
        if CLIENT_ID is None or CLIENT_ID == '' or CLIENT_SECRET is None or CLIENT_SECRET == '' or MARKET_CLIENT_ID is None or MARKET_CLIENT_ID == '':
            raise PluginError('Missing informations. Either CLIENT_ID, SECRET_ID or MARKET_CLIENT_ID in the plugin configuration are missing. Please contact the system administrator.')

    # After validating the product spec and saving the asset info in the database
    def on_post_product_spec_validation(self, provider, asset):
        asset.meta_info['market_id'] = MARKET_CLIENT_ID

        tenant_manager_client = TenantManagerClient()
        # fiware-service is the tenant for whom the product is to be created
        tenant_info = tenant_manager_client.get_tenant(asset.meta_info['service'])

        # Check that the user making the request is authorized to create an offering for the tenant
        if provider.private:
            # If the user making the request is a user, he must be the owner
            if tenant_info['owner_id'] != provider.name:
                raise PluginError('You are as user ' + provider.name + ' not authorized to publish an product for ' + tenant_info['name'])
        else:
            # if the user making the request is an organization, it must be the tenant organization
            if tenant_info['tenant_organization'] != provider.name:
                raise PluginError('You are as user ' + provider.name + ' not authorized to publish an product for ' + tenant_info['name'])

        if asset.meta_info['ngsi_type'] == 'NGSIv2' and header_type[0] == 'application/json':
            asset.save()
        elif asset.meta_info['ngsi_type'] == 'NGSI-LD' and header_type[0] == 'application/ld+json':
            asset.save()
        else:
            raise PluginError('Error by selecting the media type. NGSIv2 needs application/json and NGSI-LD needs application/ld+json as media type.')

    # Buying the product (checkout action)
    def on_product_acquisition(self, asset, contract, order):
        # Assign buyer in keyrock the product specific role to grant access to the data
        keyrock_client = KeyrockClient()
        keyrock_client.grant_permission(asset.meta_info['market_id'], order.customer, asset.meta_info['role'])

        # Assign buyer in tenant-manager to the tenant and the specific role to grant access to the api
        tenant_manager_client = TenantManagerClient()
        tenant_manager_client.grant_permission(asset.meta_info['service'], order.customer, order.owner_organization)

    def on_product_suspension(self, asset, contract, order):
        keyrock_client = KeyrockClient()
        keyrock_client.revoke_permission(asset.meta_info['market_id'], order.customer, asset.meta_info['role'])

        tenant_manager_client = TenantManagerClient()
        tenant_manager_client.revoke_permission(asset.meta_info['service'], order.customer, order.owner_organization)

    def get_usage_specs(self):
        return self._units

    def get_pending_accounting(self, asset, contract, order):
        return []
