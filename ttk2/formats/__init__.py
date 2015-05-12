import json
import polib
from collections import OrderedDict
from xml.etree import ElementTree
from . import jproperties


class Store:
	DEFAULT_ENCODING = "utf-8"
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
		self.occurrences = []
		self.context = ""
		self.obsolete = False

	def __repr__(self):
		return "<Unit %r: %s>" % (self.key, self.value)


class POStore(Store):
	def read(self, file, lang):
		po = polib.pofile(file.read())
		lang = po.metadata.get("Language", lang)
		for entry in po:
			unit = Unit(entry.msgid, entry.msgstr)
			unit.lang = lang
			unit.context = entry.msgctxt
			unit.comment = entry.comment
			unit.translator_comment = entry.tcomment
			unit.obsolete = entry.obsolete
			unit.occurrences = entry.occurrences[:]
			self.units.append(unit)

	def serialize(self):
		po = polib.POFile()
		for unit in self.units:
			occurences = unit.occurrences[:]
			entry = polib.POEntry(
				msgid = unit.key,
				msgstr = unit.value,
				comment = getattr(unit, "comment", ""),
				tcomment = getattr(unit, "translator_comment", ""),
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


class PropertiesStore(Store):
	def read(self, file, lang):
		props = jproperties.Properties()
		props.load(file)
		comment = None
		for node in props.nodes:
			if isinstance(node, jproperties.Comment):
				comment = node
			elif isinstance(node, jproperties.Property):
				unit = Unit(node.key, node.value)
				unit.lang = lang
				if comment:
					unit.comment = comment
					comment = None
				self.units.append(unit)

	def serialize(self):
		props = jproperties.Properties()
		for unit in self.units:
			if hasattr(unit, "comment"):
				props.nodes.append(jproperties.Comment(unit.comment))
			props[unit.key] = unit.value

		return str(props)


class TSStore(Store):
	VERSION = "2.1"

	def read(self, file, lang):
		xml = ElementTree.parse(file)
		lang = xml.getroot().attrib["language"]
		for context in xml.findall("context"):
			context_name = context.findtext("name")
			for message in context.findall("message"):
				source = message.findtext("source")
				translation = message.find("translation")

				unit = Unit(source, translation.text or "")
				unit.lang = lang
				unit.context = context_name
				for location in message.findall("location"):
					unit.occurrences.append((
						location.attrib["filename"],
						location.attrib["line"],
					))
				if translation.attrib.get("type") == "obsolete":
					unit.obsolete = True
				self.units.append(unit)

	def _element(self, name, append_to, text=""):
		e = ElementTree.Element(name)
		if text:
			e.text = text
		append_to.append(e)
		return e

	def _pretty_print(self, input):
		from xml.dom import minidom
		xml = minidom.parseString(input)
		# passing an encoding to toprettyxml() makes it return bytes... sigh.
		return str(xml.toprettyxml(encoding=self.DEFAULT_ENCODING), encoding=self.DEFAULT_ENCODING)

	def serialize(self):
		root = ElementTree.Element("TS")
		root.attrib["version"] = self.VERSION
		# NOTE: We assume all units are the same language for now
		root.attrib["language"] = self.units[0].lang
		contexts = {}
		for unit in self.units:
			if unit.context not in contexts:
				e = self._element("context", root)
				ce = self._element("name", e, text=unit.context)
				contexts[unit.context] = e

			unit_element = self._element("message", contexts[unit.context])
			source = self._element("source", unit_element, text=unit.key)
			if hasattr(unit, "comment"):
				comment = self._element("comment", unit_element, text=unit.comment)
			translation = self._element("translation", unit_element, text=unit.value)
			if unit.obsolete:
				translation.attrib["type"] = "obsolete"

		return self._pretty_print(ElementTree.tostring(root))
