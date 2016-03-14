# ansible-jail
Ansible module to configure jails

# Tests
Test playbooks should go in ./tests. The playbook only needs the `hosts` and
`tasks` section, and hosts should be set to `all`. Running `make test` will
start a VM for each playbook and save the output of the Ansible run, 
`/etc/rc.conf`, and `/etc/jail.conf` to `tmp/testname`. 

# To build Ansible docs:
If you don't have docbook on your computer, you'll need that first.
    
    brew install docbook

Run `make builddocs` to build docs and `make viewdocs` to build and view the
documentation for the jail module in your browser. Building the documentation
takes forever.
