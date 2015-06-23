#!/usr/bin/env python
from argparse import ArgumentParser
from ttk2.conversion import convert


def main():
	import sys

	arguments = ArgumentParser(prog="ttk convert")
	arguments.add_argument("--template", type=str, dest="template",
		help="Template for bilingual conversion", nargs=1)
	arguments.add_argument("outfile", nargs=1)
	arguments.add_argument("infile", nargs="+")
	args = arguments.parse_args(sys.argv[1:])
	convert(args.outfile[0], args.infile, template=args.template)

if __name__ == "__main__":
	main()
