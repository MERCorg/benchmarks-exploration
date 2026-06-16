#!/usr/bin/env python3
"""Compare .aut files grouped by filename prefix using ltscompare -ebisim."""

import argparse
import os
import subprocess
import sys
from collections import defaultdict


def find_aut_files(directory):
	"""Return all .aut files in the given directory."""
	files = []
	for entry in os.scandir(directory):
		if not entry.is_file():
			continue

		extension = os.path.splitext(entry.name)[1].lower()
		if extension != '.aut':
			continue

		files.append(entry.path)
	return sorted(files)


def validate_aut_file(ltsinfo_bin, path):
	"""Run ltsinfo on a .aut file. Returns (valid: bool, output: str)."""
	result = subprocess.run([ltsinfo_bin, path], capture_output=True, text=True)
	output = (result.stdout + result.stderr).strip()
	return result.returncode == 0, output


def filter_valid_aut_files(ltsinfo_bin, paths):
	"""Keep only valid .aut files, warning about invalid ones."""
	valid_paths = []
	for path in paths:
		is_valid, output = validate_aut_file(ltsinfo_bin, path)
		if is_valid:
			valid_paths.append(path)
			continue

		print(f'[WARN] Ignoring invalid .aut file: {os.path.relpath(path)}')
		if output:
			for line in output.splitlines():
				print(f'       {line}')

	return valid_paths


def group_by_prefix(paths):
	"""Group file paths by filename prefix before the final underscore."""
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
	cmd = [ltscompare_bin, '-ebisim', '--tau=i', file_a, file_b]
	result = subprocess.run(cmd, capture_output=True, text=True)
	output = (result.stdout + result.stderr).strip()
	equivalent = result.returncode == 0
	return equivalent, output


def main():
	parser = argparse.ArgumentParser(
		description=(
			'Compare .aut files from two directories, grouped by prefix, '
			'using ltscompare -ebisim.'
		)
	)
	parser.add_argument('lts_dir_a', help='First directory containing .aut files')
	parser.add_argument('lts_dir_b', help='Second directory containing .aut files')
	parser.add_argument(
		'--mcrl2-bin',
		default='',
		help='Directory containing the ltscompare and ltsinfo binaries (default: use PATH)',
	)
	args = parser.parse_args()

	ltscompare_bin = (
		os.path.join(args.mcrl2_bin, 'ltscompare') if args.mcrl2_bin else 'ltscompare'
	)
	ltsinfo_bin = os.path.join(args.mcrl2_bin, 'ltsinfo') if args.mcrl2_bin else 'ltsinfo'

	if not os.path.isdir(args.lts_dir_a):
		print(f'ERROR: {args.lts_dir_a} is not a directory', file=sys.stderr)
		sys.exit(1)
	if not os.path.isdir(args.lts_dir_b):
		print(f'ERROR: {args.lts_dir_b} is not a directory', file=sys.stderr)
		sys.exit(1)

	paths_a = filter_valid_aut_files(ltsinfo_bin, find_aut_files(args.lts_dir_a))
	paths_b = filter_valid_aut_files(ltsinfo_bin, find_aut_files(args.lts_dir_b))
	paths = sorted(paths_a + paths_b)
	if not paths:
		print('No valid .aut files found in either directory.', file=sys.stderr)
		sys.exit(1)

	groups = group_by_prefix(paths)
	print(
		f'Found {len(paths)} .aut file(s) in {len(groups)} group(s) '
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
		print('All .aut files within each group are equivalent.')
	else:
		print('ERROR: Some .aut files differ (see [DIFF] entries above).')
		sys.exit(1)


if __name__ == '__main__':
	main()
