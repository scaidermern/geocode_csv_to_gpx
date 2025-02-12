#!/usr/bin/env python3
"""read addresses from CSV, use a geocoder to obtain their coordinates
and write them to a GPX file
"""

import argparse
import csv
import json
import sys
import urllib.request

from dataclasses import dataclass, field
from xml.sax.saxutils import escape

@dataclass
class Place:
    """Place information, including address and additional data
    
    Attributes:
        lineno (int): Original line number in CSV file
        addr (list): Address parts (city, street, house number etc.)
        name (str): Place name
        desc (str): Place description
        coords (list): Coordinates (tuple of longitude, latitude)
    """

    lineno: int
    addr: list
    name: str
    desc: str
    coords: list = field(default_factory=list)

@dataclass
class GeocodeCsvToGPX:
    """CSV address to GPX converter

    Attributes:
        files (list): List of CSV files to parse
        outfile (str): GPX output file name
        addr_cols (list): List of columns to read address from (starting at 0)
        name_cols (list): List of columns to use as name (starting at 0)
        desc_cols (list): List of columns to use as description (starting at 0)
        skip_first_lines (int): Skip the first N lines
        dryrun (bool): Skip geocoding part, just print addresses
        verbose (bool): Print debugging information
        places (list): List of places (addresses with coordinates and additional information)
    """

    files: list
    outfile: str
    addr_cols: list = field(default_factory=list)
    name_cols: list = field(default_factory=list)
    desc_cols: list = field(default_factory=list)
    skip_first_lines: int = 0
    dryrun: bool = False
    verbose: bool = False
    places: list = field(default_factory=list)

    def run(self):
        """Perform all the magic"""

        if self.verbose:
            print('Reading CSV file')

        for file in self.files:
            self.places += self.get_places_from_csv(file)

        if self.dryrun or self.verbose:
            for place in self.places:
                print(place)
            if self.dryrun:
                return

        if self.verbose:
            print(f'Obtaining coordinates for {len(self.places)} places')
        self.get_coordinates()

        if self.verbose:
            print('Writing GPX file')
        self.write_places_to_gpx()

    def get_places_from_csv(self, path):
        """Return all places defined in CSV file"""

        places = []
        with open(path, encoding='utf-8') as file:
            for lineno, columns in enumerate(
                    csv.reader(file, skipinitialspace=True), start=1):
                if self.skip_first_lines and lineno <= self.skip_first_lines:
                    continue
                place = self.get_place_from_line(columns, lineno)
                if place:
                    places.append(place)

        return places

    def get_place_from_line(self, columns, lineno):
        """Parse place from single line from CSV file"""

        if 0 == len(columns):
            return None

        # obtain place information from columns
        addr = self.get_columns(columns, self.addr_cols, ', ')
        name = self.get_columns(columns, self.name_cols, ' ')
        desc = self.get_columns(columns, self.desc_cols, ', ')

        # validate place information
        if not name or not addr:
            print(f'Skipping place from line number {lineno} without '
                  f'name ({name}) or address ({addr})')
            return None

        return Place(lineno=lineno, addr=addr, name=name, desc=desc)

    def get_columns(self, cols, subset, delimiter):
        """Obtain a subset of the given columns and concatenate them
        with the given delimiter"""

        result = ''
        if not subset:
            # no column subset for this type of information specified
            return result

        for col in subset:
            col -= 1 # user-specified indices start at 1
            if col >= len(cols):
                break
            result += delimiter if result else ''
            result += cols[col]
        return result

    def get_coordinates(self):
        """Add coordinates to all places"""

        for place in self.places:
            # try to geocode 'name, address'
            coords = self.geocode_address(f'{place.name}, {place.addr}')
            if not coords:
                # try to geocode address only
                coords = self.geocode_address(place.addr)
            if not coords:
                print(f'Could not obtain coordinates for place {place.name} from '
                      f'line number {place.lineno} with address: {place.addr}')
                continue

            place.coords = coords

    def geocode_address(self, address):
        """Obtain coordinates for given address
        Return tuple of longitude, latitude or None if geocoding fails
        """

        # OSM-based geocoder Photon
        geocoder = 'https://photon.komoot.io/api/?q=%s&limit=1'

        try:
            if self.verbose:
                print(f'Performing geocoding for address {address}')

            request = urllib.request.Request(
                url=geocoder % urllib.parse.quote(address),
                headers={'User-Agent': 'geocodeCsvToGpx/1.0'})
            with urllib.request.urlopen(request) as response:
                data = json.load(response)
                if data['features']:
                    coords = data['features'][0]['geometry']['coordinates']
                    if self.verbose:
                        print(f'Coordinates: {coords}')
                    return coords
        except Exception as ex:
            print(f'Geocoding for address {address} failed: {ex}')

        # no result
        return None

    def xml_escape(self, text):
        """Escape text to valid XML"""

        return escape(text, entities={
            # additionally escape apostrophe and quotes
            "'": "&apos;",
            "\"": "&quot;"
        })

    def write_places_to_gpx(self):
        """Write all places with their coordinates to a GPX file"""

        with open(self.outfile, 'w', encoding='utf-8') as file:
            # write GPX header
            file.write(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<gpx version="1.1">\n'
            )

            # write places as GPX waypoints
            for place in self.places:
                if not place.coords:
                    # geocoding failed previously
                    continue

                file.write(
                    f'  <wpt lon="{place.coords[0]}" lat="{place.coords[1]}">\n'
                    f'    <name>{self.xml_escape(place.name)}</name>\n')
                if place.desc:
                    file.write(f'    <desc>{self.xml_escape(place.desc)}</desc>\n')
                file.write('  </wpt>\n')

            # write GPX trailer
            file.write('</gpx>\n')

def main() -> int:
    """main"""

    parser = argparse.ArgumentParser(
        prog='Geocode CSV to GPX',
        description='read addresses from CSV, use a geocoder to obtain'
            ' their coordinates and write them to a GPX file\n\n'
            'note: all indices (columns, lines) start at 1',
        epilog=f'example: {sys.argv[0]} -n 6 -a 3 7 -d 11 -o places.gpx input.csv',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('files', nargs='*', help='CSV files to read')
    parser.add_argument('-o', '--outfile', required=True, help='GPX output file')
    parser.add_argument('-a', '--address', nargs='+', type=int, required=True,
        help='list of columns to read address from')
    parser.add_argument('-n', '--name', nargs='+', type=int, required=True,
        help='list of columns to use as name')
    parser.add_argument('-d', '--desc', nargs='+', type=int,
        help='list of columns to use as description')
    parser.add_argument('-s', '--skip-first-lines', type=int, help='skip the first NUM lines')
    parser.add_argument('-g', '--dry-run', action='store_true',
        help='skip geocoding part, just print parsed addresses and descriptions')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='print debugging information')

    args = parser.parse_args()

    converter = GeocodeCsvToGPX(args.files, args.outfile, args.address, args.name,
        args.desc, args.skip_first_lines, args.dry_run, args.verbose)
    converter.run()

    return 0

if __name__ == '__main__':
    sys.exit(main())
