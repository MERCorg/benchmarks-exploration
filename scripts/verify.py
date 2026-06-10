#!/usr/bin/env python3
"""Compare LTS files grouped by identical prefix using ltscompare -ebisim."""

import argparse
import os
import subprocess
import sys
from collections import defaultdict


def find_lts_files(directory):
	"""Return all .aut and .lts files in the given directory."""
	supported = ('.aut', '.lts')
	files = []
	for entry in os.scandir(directory):
		if entry.is_file() and os.path.splitext(entry.name)[1].lower() in supported:
			files.append(entry.path)
	return sorted(files)


def group_by_prefix(paths):
	"""Group file paths by their prefix (stem split on the last underscore)."""
	groups = defaultdict(list)
	for path in paths:
		stem = os.path.splitext(os.path.basename(path))[0]
		underscore_pos = stem.rfind('_')
		if underscore_pos == -1:
			prefix = stem
		else:
			prefix = stem[:underscore_pos]
		groups[prefix].append(path)
	return dict(groups)


def compare_lts(ltscompare_bin, file_a, file_b):
	"""Run ltscompare -ebisim on two files. Returns (equivalent: bool, output: str)."""
	cmd = [ltscompare_bin, '-ebisim', file_a, file_b]
	result = subprocess.run(cmd, capture_output=True, text=True)
	output = (result.stdout + result.stderr).strip()
	equivalent = result.returncode == 0
	return equivalent, output


def main():
	parser = argparse.ArgumentParser(
		description=(
			'Compare LTS files from two directories, grouped by prefix, '
			'using ltscompare -ebisim.'
		)
	)
	parser.add_argument('lts_dir_a', help='First directory containing LTS (.aut/.lts) files')
	parser.add_argument('lts_dir_b', help='Second directory containing LTS (.aut/.lts) files')
	parser.add_argument(
		'--mcrl2-bin',
		default='',
		help='Directory containing the ltscompare binary (default: use PATH)',
	)
	args = parser.parse_args()

	ltscompare_bin = (
		os.path.join(args.mcrl2_bin, 'ltscompare') if args.mcrl2_bin else 'ltscompare'
	)

	if not os.path.isdir(args.lts_dir_a):
		print(f'ERROR: {args.lts_dir_a} is not a directory', file=sys.stderr)
		sys.exit(1)
	if not os.path.isdir(args.lts_dir_b):
		print(f'ERROR: {args.lts_dir_b} is not a directory', file=sys.stderr)
		sys.exit(1)

	paths_a = find_lts_files(args.lts_dir_a)
	paths_b = find_lts_files(args.lts_dir_b)
	paths = sorted(paths_a + paths_b)
	if not paths:
		print('No LTS files found in either directory.', file=sys.stderr)
		sys.exit(1)

	groups = group_by_prefix(paths)
	print(
		f'Found {len(paths)} LTS file(s) in {len(groups)} group(s) '
		f'({len(paths_a)} in dir A, {len(paths_b)} in dir B).\n'
	)

	all_ok = True
	for prefix in sorted(groups):
		members = groups[prefix]
		if len(members) < 2:
			print(f'[SKIP] {prefix}: only one file across both directories.')
			continue

		reference = members[0]
		for other in members[1:]:
			equivalent, output = compare_lts(ltscompare_bin, reference, other)
			ref_name = os.path.relpath(reference)
			other_name = os.path.relpath(other)
			if equivalent:
				print(f'[OK]   {prefix}: {ref_name} ~ {other_name}')
			else:
				print(f'[DIFF] {prefix}: {ref_name} != {other_name}')
				if output:
					for line in output.splitlines():
						print(f'       {line}')
				all_ok = False

	print()
	if all_ok:
		print('All LTS files within each group are equivalent.')
	else:
		print('ERROR: Some LTS files differ (see [DIFF] entries above).')
		sys.exit(1)


if __name__ == '__main__':
	main()
