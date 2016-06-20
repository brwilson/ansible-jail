#!/usr/bin/python

# TODO: Put in copyright/licensing

DOCUMENTATION = """
"""

EXAMPLES = """
"""


import re


def generate_jail_conf(module):
    """Generate config stanza for jail.

    Args:
        module (AnsibleModule): the module object for this jail

    Returns:
        list of lines comprising the jail's config stanza
    """
    if module.params['state'] == 'absent':
        return []

    params = {
        'path': module.params['path'],
        'ip4.addr': module.params['ip4_addr'],
        'interface': module.params['interface'],
        'host.hostname': module.params['host_hostname'],
        'exec.start': module.params['exec_start'],
        'exec.stop': module.params['exec_stop'],
        'securelevel': module.params['securelevel'],
        'mount.devfs': module.params['mount_devfs']
    }
    params.update(module.params['other_config'])

    config = []
    config.append('#AnsibleJailBegin:{}\n'.format(module.params['name']))
    config.append('{} {{\n'.format(module.params['name']))

    for key in sorted(params.keys()):
        if params[key] is not None:
            config.append('    "{key}" = "{value}";\n'.format(key=key, value=params[key]))

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
    try:
        with open(module.params['conf_file'], 'r') as f:
            config = f.readlines()
    except IOError as e:
        # errno 2 = file doesn't exist
        if e.errno == 2:
            config = []
        else:
            raise

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
    if jail_config and jail_config[-1] != jail_end:
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


def write_jail_conf(module):
    """Set configuration for a jail.

    Args:
        module (AnsibleModule): the module object for this jail

    Returns:
        None
    """

    try:
        with open(module.params['conf_file'], 'r') as f:
            all_conf = f.readlines()
    except IOError as e:
        # errno 2 = file doesn't exist
        if e.errno == 2:
            all_conf = []
        else:
            raise

    jail_conf = get_jail_conf(module)
    if jail_conf:
        jail_begin = all_conf.index(jail_conf[0])
        jail_end = all_conf.index(jail_conf[-1])
        all_conf[jail_begin:jail_end + 1] = generate_jail_conf(module)
    else:
        all_conf.extend(generate_jail_conf(module))

    try:
        with open(module.params['conf_file'], 'w') as f:
            f.writelines(all_conf)
    except IOError:
        msg = "Unable to open {} for writing.".format(module.params['rc_file'])
        module.fail_json(msg=msg)


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
               "the rc file you specified?")
        module.fail_json(msg=msg)

    write_rc_jail_list(module, jail_list)


def write_rc_jail_list(module, jail_list):
    """Modify the jail_list variable in the specified rc file.

    Args:
        module (AnsibleModule): the module object
        jail_list (list): names of jails to set jail_list to
    Returns:
        None
    """

    try:
        with open(module.params['rc_file'], 'r') as f:
            rc_conf = []
            rc_conf = f.readlines()
    except IOError as e:
        # errno 2 = file doesn't exist
        if e.errno == 2:
            rc_conf = []
        else:
            msg = "Unable to open {} for reading.".format(module.params['rc_file'])
            module.fail_json(msg=msg)

    new_rc_conf = []
    new_jail_list = 'jail_list="{}"\n'.format(' '.join(jail_list))

    # loop through lines in rc_file and replace the jail_list variable
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
        with open(module.params['rc_file'], 'w') as f:
            f.writelines(new_rc_conf)
    except IOError:
        msg = "Unable to open {} for writing.".format(module.params['rc_file'])
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
            securelevel=dict(default=0, type='int', choices=[-1, 0, 1, 2, 3]),
            mount_devfs=dict(default=True, type='bool'),
            other_config=dict(default={}, type='dict'),
            conf_file=dict(default='/etc/jail.conf', type='str'),
            rc_file=dict(default='/etc/rc.conf', type='str'),
            enabled=dict(default=True, type='bool'),
            state=dict(default='present', type='str', choices=['present', 'absent'])
        ),
        supports_check_mode=False
    )

    # TODO
    # make ipv4_addr and interface require the other if one is provided

    if not module.params['host_hostname']:
        module.params['host_hostname'] = module.params['name']

    if get_platform() != 'FreeBSD':
        module.fail_json(msg='This module is only compatible with FreeBSD.')

    result = {'changed': False}

    # Make any required directories if they don't exist
    dirpaths = [
        os.path.dirname(module.params['conf_file']),
        os.path.dirname(module.params['rc_file'])
    ]

    for d in dirpaths:
        try:
            if not os.path.exists(d):
                os.makedirs(d)
                result['changed'] = True
        except IOError:
            msg = "Unable to create {}.".format(d)
            module.fail_json(msg=msg)

    # Update config file
    if not test_jail_conf(module):
        result['changed'] = True
        write_jail_conf(module)

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
if __name__ == '__main__':
    main()
