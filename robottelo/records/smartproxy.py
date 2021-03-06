# -*- encoding: utf-8 -*-

"""
Module for Smart proxy api an record implementation
"""


from robottelo.api.apicrud import ApiCrud
from robottelo.common.helpers import get_server_url
from robottelo.common import records


class SmartProxyApi(ApiCrud):
    """ Implementation of api for  foreman SmartProxy
    """
    api_path = "/api/v2/smart_proxies"
    api_json_key = u"smart_proxy"

    create_fields = ["name",
                     "url"]


class SmartProxy(records.Record):
    """ Implementation of foreman SmartProxy record
    We asume, that main server has smart proxy configured.
    """
    name = records.StringField()
    url = records.StringField(default=get_server_url())

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = SmartProxyApi
