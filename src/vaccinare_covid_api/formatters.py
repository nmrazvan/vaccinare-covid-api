import csv
import json
from datetime import datetime, date


class CsvFormatter:
    def __init__(self, file, header):
        self.file = file
        self.writer = csv.writer(file)
        self.header = header
        self._current_row_identifier = None
        self._current_row = None

        self.aggregation_keys = {}
        for idx, key in enumerate(self.header.keys()):
            if key[-2:] == "[]":
                self.aggregation_keys[key] = idx

    def start(self):
        self.writer.writerow(self.header.values())
        self.file.flush()

    def _get_value(self, record, property_path):
        to_set = False
        if property_path[-2:] == "[]":
            to_set = True
            property_path = property_path[0:-2]

        for key in property_path.split("."):
            if type(record) is dict:
                record = record.get(key)
            else:
                record = getattr(record, key)()

        if isinstance(record, datetime):
            record = record.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(record, date):
            record = record.strftime("%Y-%m-%d")

        if to_set:
            record = {record}

        return record

    def write(self, centre, slot):
        record = {"centre": centre,
                  "slot": slot}

        row = []
        row_identifier = []
        for key in self.header.keys():
            val = self._get_value(record, key)
            row.append(val)
            if key not in self.aggregation_keys:
                row_identifier.append(val)

        if self._current_row_identifier:
            if self._current_row_identifier != row_identifier:
                self._flush_current_record()
            else:
                for idx in self.aggregation_keys.values():
                    self._current_row[idx].update(row[idx])

        if not self._current_row_identifier:
            self._current_row = row
            self._current_row_identifier = row_identifier

    def end(self):
        self._flush_current_record()

    def _flush_current_record(self):
        csv_row = []
        for value in self._current_row:
            if type(value) is set:
                value = ";".join(sorted(value))
            csv_row.append(value)
        self.writer.writerow(csv_row)
        self.file.flush()
        self._current_row = None
        self._current_row_identifier = None


class JsonFormatter:
    def __init__(self, file):
        self.file = file
        self.had_first_record = False

    def start(self):
        self.file.write("[")

    def write(self, centre, slot):
        if self.had_first_record:
            self.file.write(",")
        else:
            self.had_first_record = True
        self.file.write(json.dumps({"centre": centre, "slot": slot}, default=str))

    def end(self):
        self.file.write("]")
