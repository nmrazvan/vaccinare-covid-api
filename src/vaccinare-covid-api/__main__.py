import argparse
import json
import sys

from .client import VaccinareCovidApi, CsvWriter
from .storage import GoogleDriveUploader


def get_counties(client, _args):
    print(json.dumps(client.get_counties(), indent=4))


def get_available_slots(client, args):
    if args.upload_to_gdrive and not args.file:
        raise Exception("You need to specify and output file when uploading to Google Drive")

    file = sys.stdout
    if args.file:
        file = open(args.file, "w")

    if args.format == "csv":
        writer = CsvWriter(file)
    else:
        raise Exception(f"Invalid output format: {args.format}")
    writer.start()

    for centre, slot in client.get_available_slots_for_all_centres(args.months):
        writer.write(centre, slot)
    writer.end()

    if file is not sys.stdout:
        file.close()

    if args.upload_to_gdrive:
        gdrive_uploader = GoogleDriveUploader()
        gdrive_uploader.upload(args.file, args.gdrive_document_title)


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda _client, _args: parser.print_help())
    subparsers = parser.add_subparsers()

    gc_parser = subparsers.add_parser("get-counties")
    gc_parser.set_defaults(func=get_counties)

    gas_parser = subparsers.add_parser("get-available-slots")
    gas_parser.add_argument("--format", default="csv", choices=["csv"], help="Output format")
    gas_parser.add_argument("--months", default=2, help="Number of months to be checked")
    gas_parser.add_argument("--county-id", help="County ID. "
                                                "See https://programare.vaccinare-covid.gov.ro/nomenclatures/api/county")
    gas_parser.add_argument("--csv-header", help="CSV header in JSON format. See CsvWriter.header")
    gas_parser.add_argument("--file", help="Path to the output file")
    gas_parser.add_argument("--upload-to-gdrive", help="Upload to Google Drive", action="store_true", default=False)
    gas_parser.add_argument("--gdrive-document-title", default="Programare vaccinare Covid - Locuri libere")
    gas_parser.set_defaults(func=get_available_slots)

    client = VaccinareCovidApi()
    args = parser.parse_args()
    args.func(client, args)


if __name__ == "__main__":
    main()
