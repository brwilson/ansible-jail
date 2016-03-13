vagrant_dirs = $(wildcard tests/*)
ansible_out = $(vagrant_dirs:=/ansible_out.txt)
etc_jail_conf = $(vagrant_dirs:=/jail.conf)
etc_rc_conf = $(vagrant_dirs:=/rc.conf)
jailfiles = $(vagrant_dirs:=/modules/jail.py)
vagrantfiles = $(vagrant_dirs:=/Vagrantfile)

all: jail.py
	
jail.py: docs/documentation.yml docs/examples.yml
	sed '/DOCUMENTATION = """/ r docs/documentation.yml' src/jail.py > jail.py
	sed -i '' '/EXAMPLES = """/ r docs/examples.yml' jail.py

test: $(ansible_out)

$(ansible_out): $(jailfiles) $(vagrantfiles)
	cd $(subst /ansible_out.txt,,$@); vagrant up; vagrant destroy -f

$(jailfiles): jail.py
	cp jail.py $@

percent = %
$(vagrantfiles):
	cp Vagrantfile.template $@
	mac=`dd bs=1 count=3 if=/dev/random 2>/dev/null | hexdump -v -e '/1 "$(percent)02X"'`; sed -i "" "s/_MACADDR_/080027$$mac/" $@

stop_vagrant:
	vagrant global-status | grep jailmodtest | awk '{print $$1}' | xargs -P12 -I{} vagrant destroy -f {}

clean: stop_vagrant
	rm -f $(jailfiles)
	rm -f $(ansible_out)
	rm -f $(vagrantfiles)
	rm -f $(etc_jail_conf)
	rm -f $(etc_rc_conf)
	rm -f jail.py

help:
	@echo 'Targets:'
	@echo ''
	@echo 'all (default):  insert documentation strings into jail.py'
	@echo 'test:           run vagrant tests'

