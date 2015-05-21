#!/usr/bin/env python
import sqlite3
from ttk2.formats import *


class SQLiteStore(Store):
	def __init__(self, dbfile=":memory:"):
		super().__init__()
		self.dbfile = dbfile
		self.connection = sqlite3.connect(self.dbfile)
		self.connection.execute("""
			CREATE TABLE IF NOT EXISTS units (
				key text,
				value text,
				location_filename text,
				location_line smallint,
				comment text not null,
				translator_comment text not null,
				context text,
				obsolete bool
			)
		""")
		self.connection.execute("""
			CREATE TABLE IF NOT EXISTS metadata (
				language text
			)
		""")

	def serialize(self):
		values = []
		for unit in self.units:
			values.append((
				unit.key,
				unit.value,
				unit.location.get("filename") if unit.location else None,
				unit.location.get("line") if unit.location else None,
				getattr(unit, "comment", ""),
				getattr(unit, "translator_comment", ""),
				unit.context,
				unit.obsolete,
			))

		self.connection.executemany("""
		INSERT INTO units VALUES (
			?, ?, ?, ?, ?, ?, ?, ?
		)""", values)

		return "\n".join(self.connection.iterdump())


if __name__ == "__main__":
	import sys
	for name in sys.argv[1:]:
		cls = guess_format(name)
		with open(name, "r") as f:
			tfile = cls()
			tfile.read(f, lang="en")

			sql = SQLiteStore.from_store(tfile)
			print(sql.serialize())
