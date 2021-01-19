import argparse
import json
import logging
import os
import sys

from .client import VaccinareCovidApi
from .storage import GoogleDriveUploader
from .formatters import CsvFormatter, JsonFormatter


def get_counties(client, _args):
    print(json.dumps(client.get_counties(), indent=4))


def get_available_slots(client, args):
    if args.upload_to_gdrive and not args.file:
        raise Exception("You need to specify and output file when uploading to Google Drive")

    file = sys.stdout
    if args.file:
        file = open(args.file, "w")

    if args.format == "csv":
        writer = CsvFormatter(file, {
            "centre.countyName": "Județ",
            "centre.localityName": "Localitate",
            "centre.name": "Centru",
            "centre.address": "Adresă centru",
            "slot.startTime": "Dată și oră",
        })
    elif args.format == "csv_by_centre":
        writer = CsvFormatter(file, {
            "centre.countyName": "Județ",
            "centre.localityName": "Localitate",
            "centre.name": "Centru",
            "centre.address": "Adresă centru",
            "slot.startTime.date[]": "Date disponibile"
        })
    elif args.format == "csv_by_date":
        writer = CsvFormatter(file, {
            "centre.countyName": "Județ",
            "centre.localityName": "Localitate",
            "centre.name": "Centru",
            "centre.address": "Adresă centru",
            "slot.startTime.date": "Dată"
        })
    elif args.format == "json":
        writer = JsonFormatter(file)
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda _client, _args: parser.print_help())
    parser.add_argument("--verbose", "-vvv", action="store_true", default=False, help="Verbose output")
    parser.add_argument("--cache-lifetime", type=int, help="Cache lifetime in seconds")
    parser.add_argument("--fallback-cache-lifetime", type=int, help="Cache lifetime in seconds")
    parser.add_argument("--cache-path", default="var/cache", help="Cache path")
    parser.add_argument("--delay-between-requests", type=float, default=0.1, help="Delay between requests in seconds")
    parser.add_argument("--max-retries", type=int, default=0, help="Max number of retries in case of failures")
    parser.add_argument("--delay-between-retries", type=float, default=1, help="Delay between retries in seconds")
    subparsers = parser.add_subparsers()

    gc_parser = subparsers.add_parser("get-counties")
    gc_parser.set_defaults(func=get_counties)

    gas_parser = subparsers.add_parser("get-available-slots")
    gas_parser.add_argument("--format", default="csv", choices=["csv", "csv_by_centre", "csv_by_date", "json"],
                            help="Output format")
    gas_parser.add_argument("--months", default=2, help="Number of months to be checked")
    gas_parser.add_argument("--file", help="Path to the output file")
    gas_parser.add_argument("--upload-to-gdrive", help="Upload to Google Drive", action="store_true", default=False)
    gas_parser.add_argument("--gdrive-document-title", default="Programare vaccinare Covid - Locuri libere")
    gas_parser.set_defaults(func=get_available_slots)

    args = parser.parse_args()

    client = VaccinareCovidApi(session_token_file=os.path.join(args.cache_path, "vaccinare_token"),
                               cache_lifetime=args.cache_lifetime,
                               fallback_cache_lifetime=args.fallback_cache_lifetime,
                               cache_path=args.cache_path,
                               delay_between_requests=args.delay_between_requests,
                               max_retries=args.max_retries,
                               delay_between_retries=args.delay_between_retries)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    args.func(client, args)


if __name__ == "__main__":
    main()
