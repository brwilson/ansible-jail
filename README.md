# ansible-jail
Ansible module to configure jails

# Tests
Test playbooks should go in a folder under ./test with the following
structure:

    ansible-jail
        tests
            my-test
                playbook.yml

# To build Ansible docs:

    brew install docbook
    export XML_CATALOG_FILES="/usr/local/etc/xml/catalog"
    cd ansible-checkout && make webdocs
