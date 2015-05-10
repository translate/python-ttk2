#!/usr/bin/env python
import os
from ttk2.formats import *


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