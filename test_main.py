#!/usr/bin/env python
import argparse
import logging
from io import StringIO
from ttk2.formats import Unit, POStore, TSStore


# The idea of this list is to reuse the API of the different implementations
# so we can test all at once if possible
_IMPLEMENTED_STORES = [POStore, TSStore]


def test_single_unit():
	unit = Unit("Translation key", "Translation value")
	unit.lang = "en-US"
	logging.debug("Serializing %s", unit)
	for implementation in _IMPLEMENTED_STORES:
		logging.debug("Testing store %s" % implementation)
		store = implementation()
		store.units.append(unit)
		output = store.serialize()
		logging.debug("Output: %s", output)
		parsed_store = implementation()
		parsed_store.read(StringIO(output), lang=None, srclang=None)
		assert len(parsed_store.units) == 1
		parsed_unit = parsed_store.units[0]
		assert parsed_unit.key == unit.key
		assert parsed_unit.value == unit.value


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--debug",
		help="Print debugging information",
		action="store_const",
		dest="loglevel",
		const=logging.DEBUG,
		default=logging.WARNING
	)
	args = parser.parse_args()
	logging.basicConfig(level=args.loglevel)
	for name, f in globals().items():
		if name.startswith("test_") and callable(f):
			f()


if __name__ == "__main__":
	main()
