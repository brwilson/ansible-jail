import unittest
from mock import mock_open, patch
import jail
import __builtin__


class ModuleTestTemplate(unittest.TestCase):
    class AnsibleModule(object):
        def __init__(self, name, path, ip4_addr=None, interface=None,
                     host_hostname=None, exec_start='/bin/sh /etc/rc',
                     exec_stop='/bin/sh /etc/rc.shutdown', securelevel=3,
                     mount_devfs=True, other_config={},
                     conf_file='/etc/jail.conf', enabled=True,
                     state='present'):
            if host_hostname is None:
                host_hostname = name
            self.params = {
                'name': name,
                'path': path,
                'ip4_addr': ip4_addr,
                'interface':  interface,
                'host_hostname': host_hostname,
                'exec_start': exec_start,
                'exec_stop': exec_stop,
                'securelevel': securelevel,
                'mount_devfs': mount_devfs,
                'other_config': other_config,
                'conf_file': conf_file,
                'enabled': enabled,
                'state': state
            }


class TestGenerateJailConfig(ModuleTestTemplate):
    def test_minimal_config(self):
        module = TestGenerateJailConfig.AnsibleModule(name='testjail1', path='/usr/local/jail/testjail1')
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            'testjail1 {\n',
            '    "path" = "/usr/local/jail/testjail1";\n',
            '    "host.hostname" = "testjail1";\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "securelevel" = "3";\n',
            '    "mount.devfs";\n',
            '}\n',
            '#AnsibleJailEnd:testjail1\n'
        ]
        generated_config = jail.generate_jail_conf(module)
        self.assertEqual(desired_config, generated_config)

    def test_other_config_config(self):
        pass


class TestGetJailConfig(ModuleTestTemplate):
    def setUp(self):
        self.module = TestGenerateJailConfig.AnsibleModule(name='testjail1', path='/usr/local/jail/testjail1')

    def test_minimal_config(self):
        desired_config = [
            '#AnsibleJailBegin:testjail1\n',
            'testjail1 {\n',
            '    "path" = "/usr/local/jail/testjail1";\n',
            '    "host.hostname" = "testjail1";\n',
            '    "exec.start" = "/bin/sh /etc/rc";\n',
            '    "exec.stop" = "/bin/sh /etc/rc.shutdown";\n',
            '    "securelevel" = "3";\n',
            '    "mount.devfs";\n',
            '}\n',
            '#AnsibleJailEnd:testjail1\n'
        ]
        jail_config = '''#AnsibleJailBegin:testjail1
testjail1 {
    "path" = "/usr/local/jail/testjail1";
    "host.hostname" = "testjail1";
    "exec.start" = "/bin/sh /etc/rc";
    "exec.stop" = "/bin/sh /etc/rc.shutdown";
    "securelevel" = "3";
    "mount.devfs";
}
#AnsibleJailEnd:testjail1
#AnsibleJailBegin:testjail2
testjail2 {
    "path" = "/usr/local/jail/testjail2";
    "host.hostname" = "testjail2";
    "exec.start" = "/bin/sh /etc/rc";
    "exec.stop" = "/bin/sh /etc/rc.shutdown";
    "securelevel" = "3";
    "mount.devfs";
}
#AnsibleJailEnd:testjail2
'''

        with patch.object(__builtin__, 'open', mock_open(read_data=jail_config)):
            loaded_config = jail.get_jail_conf(self.module)

        self.assertEqual(desired_config, loaded_config)
