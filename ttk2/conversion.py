import logging
from ttk2.formats import guess_format


def convert(outfile, infile_list, template=None):
	"""
	Parse a list of config files, merge them and write the result in the desired output file.

	In the beginning, check that infile_list is not a single string, otherwise we would iterate
	over the string characters. If this is indeed a string, log a warning and create a list with
	this one element to keep going.
	"""
	if isinstance(infile_list, str):
		infile_list = [infile_list]
		logging.warning("Convert should be provided with a LIST of input files.")

	instores = []
	for path in infile_list:
		cls = guess_format(path)
		store = cls()
		with open(path, "r") as input_file:
			store.read(input_file, lang="todo")
		instores.append(store)

	if template:
		path = template[0]
		cls = guess_format(path)
		template_cls = cls()
		with open(path, "r") as template_file:
			template_file.read(template_file, lang="todo")
	else:
		template_cls = None

	outstore = guess_format(outfile)()
	for store in instores:
		for unit in store.units:
			outstore.units.append(unit)

	if template_cls:
		tunits = []
		for unit in template_cls.units:
			unit.propkey = unit.key
			unit.key = unit.value
			unit.value = ""
			tunits.append(unit)

		for unit in outstore.units:
			for tunit in tunits:
				if unit.key == tunit.propkey:
					tunit.value = unit.value

		outstore.units = tunits

	with open(outfile, "w") as output_file:
		output_file.write(outstore.serialize())
