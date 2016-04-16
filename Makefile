all: jail.py
	
jail.py: docs/documentation.yml docs/examples.yml
	sed '/DOCUMENTATION = """/ r docs/documentation.yml' src/jail.py > jail.py
	sed -i '' '/EXAMPLES = """/ r docs/examples.yml' jail.py

test:
	cd tests && python2 -m unittest jail_tests

pbtest:
	cd tests && ansible-playbook -M ../src test_playbook.yml -vv

clean:
	rm -f jail.py
	rm -f src/*.pyc
	rm -f tests/*.pyc
