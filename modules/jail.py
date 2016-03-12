#!/usr/bin/python

# TODO: Put in copyright/licensing

DOCUMENTATION = """
"""

EXAMPLES = """
"""

RETURN = """
"""

import re


def generate_jail_conf(module):
    """Generate config stanza for jail.

    Args:
        module (AnsibleModule): the module object for this jail

    Returns:
        list of lines comprising the jail's config stanza
    """
    config = []
    config.append('#AnsibleJailBegin:{}\n'.format(module.params['name']))
    config.append('{} {{\n'.format(module.params['name']))

    # Configurable params
    config.append('    "path" = "{}";\n'.format(module.params['path']))
    if module.params['ip4_addr']:
        config.append('    "ip4.addr" = "{}";\n'.format(module.params['ip4_addr']))
    if module.params['interface']:
        config.append('    "interface" = "{}";\n'.format(module.params['interface']))
    config.append('    "host.hostname" = "{}";\n'.format(module.params['host_hostname']))
    config.append('    "exec.start" = "{}";\n'.format(module.params['exec_start']))
    config.append('    "exec.stop" = "{}";\n'.format(module.params['exec_stop']))
    config.append('    "securelevel" = "{}";\n'.format(module.params['securelevel']))
    if module.params['mount_devfs']:
        config.append('    "mount.devfs";\n')

    for key, value in module.params['other_config'].iteritems():
        # jail.conf doesn't do "value = boolean"; rather, boolean settings are
        # included if true and left out if not.
        if value is True:
            config.append('    "{key}";\n'.format(key=key))
        elif value is False:
            pass
        else:
            config.append('    "{key}" = "{value}";\n'.format(key=key, value=value))

    config.append('}\n')
    config.append('#AnsibleJailEnd:{}\n'.format(module.params['name']))
    return config


def get_jail_conf(module):
    """Get current configuration for the jail.

    Args:
        module (AnsibleModule): the module object for this jail

    Returns:
        list of lines comprising the current jail configuration, including
        the AnsibleJailBegin/End delimiters
    """
    with open(module.params['conf_file'], 'r') as f:
        config = f.readlines()

    jail_config = []
    in_jail_config = False
    jail_begin = '#AnsibleJailBegin:{}\n'
    jail_begin = jail_begin.format(module.params['name'])
    jail_end = '#AnsibleJailEnd:{}\n'
    jail_end = jail_end.format(module.params['name'])

    # locate and extract current configuration for jail
    for line in config:
        if line != jail_begin and not in_jail_config:
            continue
        elif line == jail_begin and not in_jail_config:
            in_jail_config = True
            jail_config.append(line)
        elif line != jail_end and in_jail_config:
            jail_config.append(line)
        elif line == jail_end and in_jail_config:
            jail_config.append(line)
            break
        else:
            # TODO: this probably can't occur? make more robust
            fail_msg = ('Error parsing {}! Have the "AnsibleJailBegin/End" '
                        'comments been altered?')
            module.fail_json(msg=fail_msg.format(module.params['conf_file']))
    return jail_config


def test_jail_conf(module):
    """Test if jail configuration matches requested configuration.

    Args:
        module (AnsibleModule): the module object
    Returns:
        True if jail configuration matches requested configuration
        False if jail configuration differs from requested configuration
    """
    current_config = get_jail_conf(module)
    requested_config = generate_jail_conf(module)

    if current_config == requested_config:
        return True
    else:
        return False


def set_jail_conf(module):
    """Set configuration for a jail.

    Args:
        module (AnsibleModule): the module object for this jail

    Returns:
        None
    """

    with open(module.params['conf_file'], 'r') as f:
        all_conf = f.readlines()

    jail_conf = get_jail_conf(module)
    if jail_conf:
        jail_begin = all_conf.index(jail_conf[0])
        jail_end = all_conf.index(jail_conf[-1])
        all_conf[jail_begin:jail_end + 1] = generate_jail_conf(module)
    else:
        all_conf.extend(generate_jail_conf(module))

    with open(module.params['conf_file'], 'w') as f:
        f.writelines(all_conf)


def get_rc_jail_enable(module):
    """Get value of jail_enable rc variable.

    Args:
        module (AnsibleModule): the module object
    Returns:
        True if jail_enable is set to yes
        False if jail_enable is set to no
    """

    cmd = '. /etc/rc.subr; load_rc_config jail_enable; checkyesno jail_enable'
    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
    if rc == 0:
        return True
    else:
        return False


def get_rc_jail_list(module):
    """Get jails configured to start at boot.

    Args:
        module (AnsibleModule): the module object
    Returns:
        list of jail names that are configured to start at boot
    """

    cmd = '. /etc/rc.subr; load_rc_config jail_list; printf "$jail_list"'
    rc, stdout, stderr = module.run_command(cmd, check_rc=True,
                                            use_unsafe_shell=True)
    return stdout.split()


def add_rc_jail_list(module):
    """Add jail name to jail_list rc variable

    Args:
        module (AnsibleModule): the module object
    Returns:
        None
    """

    jail_list = get_rc_jail_list(module)
    jail_list.append(module.params['name'])

    # Remove duplicate jail names and sort them
    jail_list = sorted(set(jail_list))

    write_rc_jail_list(module, jail_list)


def remove_rc_jail_list(module):
    """Remove jail name from jail_list rc variable

    Args:
        module (AnsibleModule):
    Returns:
        None
    """

    jail_list = get_rc_jail_list(module)

    try:
        jail_list.remove(module.params['name'])
    except ValueError:
        msg = ("Unable to remove jail from jail_list in rc files becuase it's "
               "already absent. Is jail_list defined somewhere other than "
               "/etc/rc.conf?")
        module.fail_json(msg=msg)

    write_rc_jail_list(module, jail_list)


# TODO: make this work when stuff is defined somewhere other than /etc/rc.conf
def write_rc_jail_list(module, jail_list):
    """Modify the jail_list variable in /etc/rc.conf

    Args:
        module (AnsibleModule): the module object
        jail_list (list): names of jails to set jail_list to in /etc/rc.conf
    Returns:
        None
    """

    try:
        with open('/etc/rc.conf') as f:
            rc_conf = f.readlines()
    except IOError:
        msg = "Unable to open /etc/rc.conf for reading."
        module.fail_json(msg=msg)

    new_rc_conf = []
    new_jail_list = 'jail_list="{}"\n'.format(' '.join(jail_list))

    # loop through lines in /etc/rc.conf and replace the jail_list variable
    # with our own, appending it to the end if it doesn't exist already
    found_jail_list = False
    for line in rc_conf:
        if re.search('^jail_list=', line):
            found_jail_list = True
            new_rc_conf.append(new_jail_list)
        else:
            new_rc_conf.append(line)
    if not found_jail_list:
        new_rc_conf.append(new_jail_list)

    try:
        with open('/etc/rc.conf', 'w') as f:
            f.writelines(new_rc_conf)
    except IOError:
        msg = "Unable to open /etc/rc.conf for writing."
        module.fail_json(msg=msg)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            path=dict(required=True, type='str'),
            ip4_addr=dict(default=None, type='str'),
            interface=dict(default=None, type='str'),
            host_hostname=dict(default=None, type='str'),
            exec_start=dict(default='/bin/sh /etc/rc', type='str'),
            exec_stop=dict(default='/bin/sh /etc/rc.shutdown', type='str'),
            securelevel=dict(default=3, type='int', choices=[-1, 0, 1, 2, 3]),
            mount_devfs=dict(default=True, type='bool'),
            other_config=dict(default={}, type='dict'),
            conf_file=dict(default='/etc/jail.conf', type='str'),
            enabled=dict(default=True, type='bool'),
            state=dict(default='present', type='str', choices=['present', 'absent'])
        ),
        supports_check_mode=False
    )

    if module.params['host_hostname'] is None:
        module.params['host_hostname'] == module.params['name']

    if get_platform() != 'FreeBSD':
        module.fail_json(msg='This module is only compatible with FreeBSD.')

    result = {'changed': False}

    # Make jail config file and any required directories if they don't exist
    if not os.path.exists(module.params['conf_file']):
        if not os.path.exists(os.path.dirname(module.params['conf_file'])):
            os.makedirs(os.path.dirname(module.params['conf_file']))
        open(module.params['conf_file'], 'a').close()
        result['changed'] = True

    # Update config file
    if not test_jail_conf(module):
        result['changed'] = True
        set_jail_conf(module)

    # Set which jails are started at boot
    if module.params['name'] in get_rc_jail_list(module):
        jail_enabled = True
    else:
        jail_enabled = False

    if (module.params['enabled'] and
            module.params['state'] == 'present' and
            not jail_enabled):
        result['changed'] = True
        add_rc_jail_list(module)
    elif (not module.params['enabled'] or
            module.params['state'] == 'absent' and
            jail_enabled):
        result['changed'] = True
        remove_rc_jail_list(module)
    else:
        # jail already in desired state
        pass

    # And we're done
    module.exit_json(**result)

from ansible.module_utils.basic import *
main()
