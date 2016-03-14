playbooks = $(notdir $(wildcard tests/*.yml))
vagrant_dirs = $(addprefix tmp/, $(subst .yml,,$(playbooks)))
ansible_out = $(addsuffix /ansible_out.txt,$(vagrant_dirs))
jailfiles = $(addsuffix /modules/jail.py,$(vagrant_dirs))
vagrantfiles = $(addsuffix /Vagrantfile,$(vagrant_dirs))
playbookfiles = $(addsuffix /playbook.yml,$(vagrant_dirs))
percent = %


# Jail Module
all: jail.py
	@echo $(test_playbooks)
	
jail.py: docs/documentation.yml docs/examples.yml
	sed '/DOCUMENTATION = """/ r docs/documentation.yml' src/jail.py > jail.py
	sed -i '' '/EXAMPLES = """/ r docs/examples.yml' jail.py


# Jail Module Testing
test: $(ansible_out)

$(ansible_out): $(jailfiles) $(vagrantfiles) $(playbookfiles)
	cd $(subst /ansible_out.txt,,$@); vagrant up; vagrant destroy -f

$(jailfiles): jail.py $(vagrant_dirs)
	cp jail.py $@

$(vagrantfiles): $(vagrant_dirs)
	cp Vagrantfile.template $@
	mac=`dd bs=1 count=3 if=/dev/random 2>/dev/null | hexdump -v -e '/1 "$(percent)02X"'`; sed -i "" "s/_MACADDR_/080027$$mac/" $@

$(playbookfiles): $(vagrant_dirs)
	cp $(patsubst tmp/%/playbook.yml,tests/%.yml,$@) $@

$(vagrant_dirs):
	mkdir -p $@/modules


# Ansible Documentation
viewdocs: ansible/docsite/htmlout
	open http://localhost:8000/jail_module.html
	cd ansible/docsite/htmlout && python -m SimpleHTTPServer

builddocs: ansible/docsite/htmlout

ansible/docsite/htmlout: ansible ansible/lib/ansible/modules/extras/cloud/misc/jail.py
	make -j -C ansible/docsite modules
	make -j -C ansible/docsite htmldocs

ansible:
	git clone git://github.com/ansible/ansible.git --recursive

ansible/lib/ansible/modules/extras/cloud/misc/jail.py: jail.py ansible
	cp jail.py ansible/lib/ansible/modules/extras/cloud/misc/jail.py


# Misc
clean:
	vagrant global-status | grep jailmodtest | awk '{print $$1}' | xargs -P12 -I{} vagrant destroy -f {}
	rm -rf tmp
	rm -rf ansible
	rm -f jail.py

help:
	@echo 'Targets:'
	@echo ''
	@echo 'all (default):  insert documentation strings into jail.py'
	@echo 'test:           run vagrant tests'
	@echo 'builddocs:      build ansible documentation including the jail docs'
	@echo 'viewdocs:       view the documentation in your default browser'
