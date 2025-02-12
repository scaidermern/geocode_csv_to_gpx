# geocodeCsvToGpx

Convert addresses from a CSV file to a GPX file.

## Description

geocodeCsvToGpx reads addresses from a CSV file, uses a geocoder to obtain their coordinations and writes them as waypoints to a GPX file.

## Options

- `files`: CSV files to read
- `-h, --help`: show this help message and exit
- `-o OUTFILE, --outfile OUTFILE`: GPX output file
- `-a ADDRESS [ADDRESS ...], --address ADDRESS [ADDRESS ...]`: list of columns to read address from
- `-n NAME [NAME ...], --name NAME [NAME ...]`: list of columns to use as name
- `-d DESC [DESC ...], --desc DESC [DESC ...]`: list of columns to use as description
- `-s SKIP_FIRST_LINES, --skip-first-lines SKIP_FIRST_LINES`: skip the first NUM lines
- `-g, --dry-run`: skip geocoding part, just print parsed addresses and descriptions
- `-v, --verbose`: print debugging information

Note: all indices (columns, lines) start at 1.

## Example

Read CSV file `input.csv`, obtain name from column `6`, obtain address from column `3` and `7` (will use `,` as separator), obtain description from column `11` and write results to `places.gpx`.
```
./geocodeCsvToGpx.py -n 6 -a 3 7 -d 11 -o places.gpx input.csv
```

# License
[GPL v3](https://www.gnu.org/licenses/gpl-3.0.html)
(c) Alexander Heinlein
