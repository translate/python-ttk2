#!/usr/bin/env python
import ast
import json
import os
from collections import OrderedDict
from xml.etree import ElementTree


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
		self.location = None
		self.context = ""

	def __repr__(self):
		return "<Unit %r: %s>" % (self.key, self.value)


class POStore(Store):
	def _parse_block(self, block):
		comment = []
		msgctxt = []
		msgid = []
		msgid_plural = []
		msgstr = []
		msgstr_plural = {}
		location = None
		last = None
		for line in block.split("\n"):
			if line.startswith("#:"):
				filename, line = line[3:].split(":")
				location = {"filename": filename, "line": line}
			elif line.startswith("#"):
				comment.append(line[1:])
			elif line.startswith("msgctxt"):
				msgctxt.append(self._read_string(line[len("msgctxt "):]))
				last = msgctxt
			elif line.startswith("msgid_plural"):
				msgid.append(self._read_string(line[len("msgid_plural "):]))
				last = msgid
			elif line.startswith("msgid"):
				msgid.append(self._read_string(line[6:]))
				last = msgid
			elif line.startswith("msgstr"):
				if line[6] == "[":
					line = line[6:]
					assert line[2] == "]", "Max 10 strings in plurals"
					i = int(line[1])
					msgstr_plural[i] = [self._read_string(line[4:])]
					last = msgstr_plural[i]
				else:
					msgstr.append(self._read_string(line[7:]))
					last = msgstr
			elif line.startswith('"'):
				last.append(self._read_string(line))

		unit = Unit("".join(msgid), "".join(msgstr))
		unit.context = "".join(msgctxt)
		unit.comment = "".join(comment)
		unit.location = location
		unit.plural_id = "".join(msgid_plural)
		unit.plurals = {}
		for k, v in msgstr_plural.items():
			unit.plurals[k] = "".join(v)

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
			ret += ["#" + line for line in comment.split("\n")]

		if unit.location:
			ret.append("#: %s:%s" % (unit.location["filename"], unit.location["line"]))
		if unit.context:
			ret.append("msgctxt %s" % (porepr(unit.context)))
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


class TSStore(Store):
	def read(self, file, lang):
		xml = ElementTree.parse(file)
		for context in xml.findall("context"):
			context_name = context.findtext("name")
			for message in context.findall("message"):
				location = message.find("location")
				source = message.findtext("source")
				translation = message.findtext("translation")

				unit = Unit(source, translation)
				unit.context = context_name
				if location is not None:
					unit.location = {
						"filename": location.attrib["filename"],
						"line": location.attrib["line"],
					}
				self.units.append(unit)

map = {
	".po": POStore,
	".pot": POStore,
	".json": JSONStore,
	".ts": TSStore,
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