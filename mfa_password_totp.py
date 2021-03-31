import logging

from keystoneauth1.identity import v3 as v3_auth

from openstack_auth.plugin import base

LOG = logging.getLogger(__name__)

__all__ = ['MfaPasswordTotpPlugin']

class MfaPasswordTotpPlugin(base.BasePlugin):

    def get_plugin(self, auth_url=None, username=None, password=None, totp=None, user_domain_name=None, **kwargs):
        if not all((auth_url, username, password, totp)):
            return None

        LOG.debug('Attempting to authenticate with time-based one time password for %s', username)

        return v3_auth.MultiFactor(
            auth_url=auth_url,
            auth_methods=['v3password', 'v3totp'],
            username=username,
            password=password,
            passcode=totp,
            user_domain_name=user_domain_name,
            unscoped=True
        )
