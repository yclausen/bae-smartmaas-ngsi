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
from settings import UNITS, CLIENT_ID, CLIENT_SECRET


class SmartMaasNGSI(Plugin):

    def __init__(self, plugin_model):
        super(SmartMaasNGSI, self).__init__(plugin_model)
        self._units = UNITS

    # Before validating the product spec contents and saving the asset info in the database
    def on_pre_product_spec_validation(self, provider, asset_t, media_type, url):
        if CLIENT_ID is None or CLIENT_ID == '' or CLIENT_SECRET is None or CLIENT_SECRET == '':
            raise PluginError('Missing informations. Either CLIENT_ID or SECRET_ID in the plugin configuration are missing. Please contact the system administrator.')

    # After validating the product spec and saving the asset info in the database
    def on_post_product_spec_validation(self, provider, asset):
        # Here user is the seller
        user = User.objects.get(username=provider.name)
        asset.meta_info['app_id'] = CLIENT_ID

        tenant_manager_client = TenantManagerClient()
        if provider.private:
            # Check if seller is assigned to the tenant in tenant-manager
            is_assigned = tenant_manager_client.check_seller_assigned_to_tenant(user, asset.meta_info['service'])
            if is_assigned is False:
                raise PluginError('You are not authorized to publish an offering without being assigned to ' + asset.meta_info['service'] + ' in the tenant-mangager.')
        else:
            # Check if the tenant organization is assigned in tenant-manager
            organisation_authorized = tenant_manager_client.check_organisation_assigned_to_tenant(user, asset.meta_info['service'])
            if organisation_authorized is False:
                raise PluginError('The organisation is not authorized to publish an offering for the specified tenant.')

        if asset.meta_info['ngsi_type'] == 'NGSIv2':
            if asset.meta_info['media_types'] == 'application/json':
                asset.save()
            else:
                raise PluginError('Error by selecting the media type. NGSIv2 needs application/json as media type.')

        if asset.meta_info['ngsi_type'] == 'NGSI-LD':
            if asset.meta_info['media_types'] == 'application/ld+json':
                asset.save()
            else:
                raise PluginError('Error by selecting the media type. NGSI-LD needs application/ld+json as media type.')

    # Buying the product (checkout action)
    def on_product_acquisition(self, asset, contract, order):
        # Assign buyer in keyrock the product specific role to grant access to the data
        keyrock_client = KeyrockClient()
        response = keyrock_client.grant_permission(asset.meta_info['app_id'], order.customer, asset.meta_info['role'])

        if response != 200:
            raise PluginError('Error occurred while trying to authorize your purchase. Please contact the seller.')

        # Assign buyer in tenant-manager to the tenant and the specific role to grant access to the api
        tenant_manager_client = TenantManagerClient()
        tenant_info = tenant_manager_client.get_tenant(asset.meta_info['service'])
        tenant_manager_client.grant_permission(asset.meta_info['service'], tenant_info, order.customer, order.owner_organization)

    def on_product_suspension(self, asset, contract, order):
        client = KeyrockClient()
        client.revoke_permission(asset.meta_info['app_id'], order.customer, asset.meta_info['role'])

    def get_usage_specs(self):
        return self._units

    def get_pending_accounting(self, asset, contract, order):
        return []
