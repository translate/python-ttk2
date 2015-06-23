#!/usr/bin/env python
import argparse
import filecmp
import logging
import os
from io import StringIO
from ttk2.conversion import convert
from ttk2.formats import Unit, POStore, TSStore


# The idea of this list is to reuse the API of the different implementations
# so we can test all at once if possible
_IMPLEMENTED_STORES = [POStore, TSStore]
_CACHE_MASK = "test/cache."
_INPUT_MASK = "test/input_files/input."
_EXPECTED_OUTPUT_MASK = "test/expected_output_files/output."


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


def test_convert_json_to_po():
	_generic_test_conversion("json", "po")


def test_convert_json_to_properties():
	_generic_test_conversion("json", "properties")


def test_convert_json_to_tmx():
	_generic_test_conversion("json", "tmx")


def test_convert_json_to_ts():
	_generic_test_conversion("json", "ts")


def test_convert_properties_to_json():
	_generic_test_conversion("properties", "json")


def test_convert_properties_to_po():
	_generic_test_conversion("properties", "po")


def test_convert_properties_to_tmx():
	_generic_test_conversion("properties", "tmx")


def test_convert_properties_to_ts():
	_generic_test_conversion("properties", "ts")


def teardown_module():
	"""Clean the cache files after all the tests have been run."""
	for file_path in os.listdir("test"):
		if "cache." in file_path:
			os.remove("test/" + file_path)


def _generic_test_conversion(input_ext, output_ext):
	"""Check the conversion from a format to another one."""
	output = _CACHE_MASK + output_ext
	expected = _EXPECTED_OUTPUT_MASK + output_ext
	inputs = [_INPUT_MASK + input_ext]
	convert(output, inputs)
	assert filecmp.cmp(output, expected)


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
	teardown_module()


if __name__ == "__main__":
	main()
