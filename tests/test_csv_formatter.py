from datetime import datetime

from vaccinare_covid_api.formatters import CsvFormatter
from io import StringIO


def test_csv_formatter_with_simple_header():
    s = StringIO()
    csv = CsvFormatter(s, {"centre.id": "ID", "slot.startTime.date": "Date"})
    csv.start()
    csv.write({"id": 76}, {"startTime": datetime.strptime("2021-02-09 19:00:00", "%Y-%m-%d %H:%M:%S")})
    csv.end()
    s.seek(0)

    lt = csv.writer.dialect.lineterminator
    assert s.read() == f"ID,Date{lt}76,2021-02-09{lt}"


def test_csv_formatter_with_centre_aggregation():
    s = StringIO()
    csv = CsvFormatter(s, {"centre.id": "ID", "slot.startTime.date[]": "Date"})
    csv.start()
    csv.write({"id": 76}, {"startTime": datetime.strptime("2021-02-09 19:00:00", "%Y-%m-%d %H:%M:%S")})
    csv.write({"id": 76}, {"startTime": datetime.strptime("2021-02-10 19:00:00", "%Y-%m-%d %H:%M:%S")})
    csv.write({"id": 77}, {"startTime": datetime.strptime("2021-02-11 19:00:00", "%Y-%m-%d %H:%M:%S")})
    csv.end()
    s.seek(0)

    lt = csv.writer.dialect.lineterminator
    assert s.read() == f"ID,Date{lt}76,2021-02-09;2021-02-10{lt}77,2021-02-11{lt}"


def test_csv_formatter_with_date_aggregation():
    s = StringIO()
    csv = CsvFormatter(s, {"centre.id": "ID", "slot.startTime.date": "Date"})
    csv.start()
    csv.write({"id": 76}, {"startTime": datetime.strptime("2021-02-09 19:00:00", "%Y-%m-%d %H:%M:%S")})
    csv.write({"id": 76}, {"startTime": datetime.strptime("2021-02-10 19:00:00", "%Y-%m-%d %H:%M:%S")})
    csv.write({"id": 77}, {"startTime": datetime.strptime("2021-02-11 19:00:00", "%Y-%m-%d %H:%M:%S")})
    csv.end()
    s.seek(0)

    lt = csv.writer.dialect.lineterminator
    assert s.read() == f"ID,Date{lt}76,2021-02-09{lt}76,2021-02-10{lt}77,2021-02-11{lt}"
