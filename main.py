#!/usr/bin/env python
import ast
import json
import os
from collections import OrderedDict


class Store:
	def __init__(self):
		self.units = []

	@classmethod
	def from_store(cls, store):
		ret = cls()
		ret.units = store.units
		return ret


class Unit:
	def __init__(self, key, value):
		self.key = key
		self.value = value

	def __repr__(self):
		return "<Unit %r: %s>" % (self.key, self.value)


class POStore(Store):
	def _parse_block(self, block):
		comment = []
		msgid = []
		msgstr = []
		last = None
		for line in block.split("\n"):
			if line.startswith("#"):
				comment.append(line[1:].strip())
			elif line.startswith("msgid"):
				msgid.append(self._read_string(line[6:]))
				last = msgid
			elif line.startswith("msgstr"):
				msgstr.append(self._read_string(line[7:]))
				last = msgstr
			elif line.startswith('"'):
				last.append(self._read_string(line))

		unit = Unit("".join(msgid), "".join(msgstr))
		unit.comment = "".join(comment)

		return unit

	def _read_string(self, s):
		# what you gonna do about it?
		return ast.literal_eval(s)

	def read(self, file, lang):
		blocks = file.read().split("\n\n")
		for block in blocks:
			unit = self._parse_block(block)
			unit.lang = lang
			if unit.key == "":
				self.header = unit
			else:
				self.units.append(unit)

	@staticmethod
	def serialize_unit(unit):
		def porepr(s):
			return '"%s"' % (s.replace("\\", "\\\\").replace(r'"', r'\"').replace("\n", "\\n"))

		ret = []
		comment = getattr(unit, "comment", "")
		if comment:
			ret += ["# " + line for line in comment.split("\n")]
		ret.append("msgid %s" % (porepr(unit.key)))
		ret.append("msgstr %s" % (porepr(unit.value)))
		return "\n".join(ret)

	def serialize(self):
		ret = []
		for unit in self.units:
			ret.append(self.serialize_unit(unit))

		return "\n\n".join(ret)



class JSONStore(Store):
	def read(self, file, lang):
		d = json.load(file)
		for key in sorted(d.keys()):
			if key == "@metadata":
				self.header = d[key]
				continue
			unit = Unit(key, d[key])
			unit.lang = lang
			self.units.append(unit)

	def serialize(self):
		ret = OrderedDict()
		for unit in self.units:
			ret[unit.key] = unit.value
		return json.dumps(ret)


map = {
	".po": POStore,
	".json": JSONStore,
}

if __name__ == "__main__":
	import sys
	for name in sys.argv[1:]:
		with open(name, "r") as f:
			_, ext = os.path.splitext(name)
			tfile = map[ext]()
			tfile.read(f, lang="en")
			#for unit in tfile.units:
			#	print(unit)

			converted = JSONStore.from_store(tfile)
			#print(converted.serialize())

			back_into_po = POStore.from_store(converted)
			#print(back_into_po.serialize())