"""
XUL-Style DTD stores

https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XUL/Tutorial/Localization
"""

from lxml.etree import DTD
from xml.sax.saxutils import escape
from .. import Store, Unit


class DTDStore(Store):
	GLOBS = [".dtd"]

	def read(self, file):
		dtd = DTD(file)
		for entity in dtd.entities():
			unit = Unit(entity.name, entity.content)
			self.units.append(unit)

	def serialize(self):
		# lxml doesn't support creating DTDs from scratch
		ret = []
		for unit in self.units:
			ret.append('<!ENTITY %s "%s">' % (unit.key, escape(unit.value)))
		return "\n".join(ret)
