# ansible-jail
Ansible module to configure jails

# Tests
Unit tests can be run with `make test`. You'll need the mock module installed.

The test playbook can be run with `make pbtest`. You'll need Ansible installed,
of course. The playbook will modify the following files, and should clean up
after itself if the tests pass. If not, you'll need to delete them manually.

- `/etc/rc.conf.d/7384283903-ansible-jail_rc.conf`
- `/usr/local/9304673409-ansible-jail_jail.conf`
