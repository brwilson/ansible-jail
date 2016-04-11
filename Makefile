all: jail.py
	
jail.py: docs/documentation.yml docs/examples.yml
	sed '/DOCUMENTATION = """/ r docs/documentation.yml' src/jail.py > jail.py
	sed -i '' '/EXAMPLES = """/ r docs/examples.yml' jail.py

unittest:
	cd src && python2 -m unittest jail_tests

clean:
	rm -f jail.py
	rm -f src/*.pyc
