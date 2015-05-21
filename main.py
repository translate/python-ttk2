#!/usr/bin/env python
from ttk2.formats import *


if __name__ == "__main__":
	import sys
	for name in sys.argv[1:]:
		cls = guess_format(name)
		with open(name, "r") as f:
			tfile = cls()
			tfile.read(f, lang="en")

			converted = tfile.__class__.from_store(tfile)
			print(converted.serialize())
