# OpenStack Horizon MFA Password+TOTP

## What is this repo?
This repository is code and instructions for enabling OpenStack Dashboard (codenamed Horizon) to login an OpenStack user who must supply a time-based one-time password (TOTP) along with the user's password. OpenStack Horizon does not natively have this functionality. When you require a TOTP along with the user's password for accessing OpenStack, logging in through Horizon simply fails.

**This repo is an alpha proof-of-concept level of work.**

This repository has a patched login form for Horizon, a Horizon authentication plugin for using the Keystone V3 MFA client to authenticate with Keystone, and instructions for patching Horizon.

**This code was tested for OpenStack stable/train deployed using Kolla-Ansible and Kolla containers, but it should work for other versions of OpenStack and other types of OpenStack deployments.**

## How to setup Multi-factor Authentication with OpenStack Identity (Keystone) service

Keystone has documentation on how to setup Multi-factor authentication (MFA) and time-based one-time passwords (TOTP).

Refer to [the documentation on setting up MFA for instructions on how to setup MFA for an individual user](https://docs.openstack.org/keystone/latest/admin/multi-factor-authentication.html#multi-factor-authentication).

Refer to [the documentation on setting up a TOTP for instructions on how to setup a TOTP for an individual user](https://docs.openstack.org/keystone/latest/admin/auth-totp.html).

## How to patch Horizon

### Login to the Kolla Horizon Docker container

**This step is only for OpenStack deployments using Kolla Docker containers**

To enter the container, run the following command:

`docker exec -it horizon /bin/bash`

After running this command, you will have a bash session opened up inside of the Docker container. Running the command and its output looks like this:

`[root@vigorous-iguana ~]# docker exec -it horizon /bin/bash
(horizon)[root@vigorous-iguana /]#`

The **(horizon)** at the start of the line means you are inside of the Docker container named "horizon".

### Add an input field to the Horizon login page

The `forms.py` file in this repo is a copy of the Horizon login form with some extra code to add an optional input field for Time-based One-time Passwords.

Copy the `forms.py` file from this repo to `/usr/lib/python3.6/site-packages/openstack_auth/forms.py`

### Add the MFA authentication plugin to Horizon's authentication plugins

The `mfa_password_totp.py` file provides a new Horizon authentication plugin that uses the Keystone Multi-factor Authentication (MFA) library to authenticate the user using a password and the TOTP entered in on the Horizon login form.

Copy the `mfa_password_totp.py` file from this repo to `/usr/lib/python3.6/site-packages/openstack_auth/plugin/mfa_password_totp.py`.

### Update Settings to use the new plugin

The Horizon Django app has to know the new plugin is available for it to use. To do this, update your `local_settings.py` file inside of Horizon to include the new plugin.

Open `/usr/share/openstack-dashboard/opensatck_dashboard/local/local_settings.py`.

Add the following snippets to the end of the file:

```
AUTHENTICATION_PLUGINS = ['openstack_auth.plugin.mfa_password_totp.MfaPasswordTotpPlugin',
'openstack_auth.plugin.password.PasswordPlugin',
                          'openstack_auth.plugin.token.TokenPlugin']

OPENSTACK_KEYSTONE_MFA_TOTP_ENABLED = True
```

`AUTHENTICATION_PLUGINS` tells Horizon what plugins are available for Horizon to use to authenticate against Keystone. With the above configuration, Horizon will try to authenticate with the `MfaPasswordTotpPlugin` first, then try to authenticate with the `PasswordPlugin`, and then try to authenticate with the `TokenPlugin`.

This means Horizon will try to authenticate with the username, password, and TOTP. If the user did not supply a TOTP at login, Horizon will skip the `MfaPasswordTotpPlugin` and try the `PasswordPlugin`.

The `TokenPlugin` is for authenticating already-logged-in users. When a user logs in successfully, Keystone gives the user a token. Horizon uses the token to authenticate against Keystone during the logged-in user's session.

**This configuration means users who are not required to provide a TOTP can login with their usernames and passwords as normal through Horizon**

The line `OPENSTACK_KEYSTONE_MFA_TOTP_ENABLED = True` tells Horizon to show the input field on the login page for Time-based One-time Password.

#### Require TOTP for all logins

To require TOTP for all logins, remove the `PasswordPlugin` from the `AUTHENTICATION_PLUGINS` list. The configuration would look like this:

```
AUTHENTICATION_PLUGINS = ['openstack_auth.plugin.mfa_password_totp.MfaPasswordTotpPlugin',
                          'openstack_auth.plugin.token.TokenPlugin']
```

This configuration would force Horizon to only try to authenticate with the `MfaPasswordTotpPlugin` and the `TokenPlugin`.

### Restart Apache

Horizon uses Apache to serve its Django application. Apache must be restarted to show any of the changes made to the Horizon Django application.

#### Restart Apache in Kolla Docker container

Run `httpd -k restart` to restart Apache inside of a Kolla Docker container.

Kolla Docker containers use `dumb-init` to manage services. `dumb-init` does not have commands for managing processes.

#### Restart Apache using systemd

Run `systemctl restart httpd` to restart Apache if you are using `systemd` in a non-containerized deployment.