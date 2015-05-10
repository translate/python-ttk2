import json
import polib
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
		self.obsolete = False

	def __repr__(self):
		return "<Unit %r: %s>" % (self.key, self.value)


class POStore(Store):
	def read(self, file, lang):
		po = polib.pofile(file.read())
		for entry in po:
			unit = Unit(entry.msgid, entry.msgstr)
			unit.context = entry.msgctxt
			unit.comment = entry.comment
			unit.obsolete = entry.obsolete
			if entry.occurrences:
				filename, line = entry.occurrences[0]
				unit.location = {"filename": filename, "line": line}
			self.units.append(unit)

	def serialize(self):
		po = polib.POFile()
		for unit in self.units:
			occurences = []
			if unit.location:
				occurences.append((unit.location["filename"], unit.location["line"]))
			entry = polib.POEntry(
				msgid = unit.key,
				msgstr = unit.value,
				comment = getattr(unit, "comment", ""),
				occurences = occurences,
				obsolete = unit.obsolete,
			)
			if unit.context:
				entry.msgctxt = unit.context

			po.append(entry)

		return str(po)


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
