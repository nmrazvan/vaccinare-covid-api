#!/usr/bin/env python3
import csv
import json
import os

import requests
import time

from datetime import datetime
from dateutil.relativedelta import relativedelta

API_URL = "https://programare.vaccinare-covid.gov.ro"
CENTRES_ENDPOINT = "/scheduling/api/centres"
MONTHLY_AVAILABILITY_ENDPOINT = "/scheduling/api/time_slots/month_available_places"
DAY_SLOTS_ENDPOINT = "/scheduling/api/time_slots/day_slots"
COUNTIES_ENDPOINT = "/nomenclatures/api/county"
DATE_FORMAT = "%d-%m-%Y %H:%M:%S.%f"


class VaccinareCovidApi:
    def __init__(self, session_token=None, delay_between_requests=0.1):
        if not session_token:
            session_token = os.getenv("VACCINARE_TOKEN")

        token_file = "var/vaccinare_token"
        if not session_token and os.path.exists(token_file):
            with open(token_file, "r") as f:
                session_token = f.read()

        if not session_token:
            raise Exception("No valid token found.\n"
                            "1. Go to https://programare.vaccinare-covid.gov.ro\n"
                            "2. Login\n"
                            "3. Get the value for the cookie called 'SESSION'\n"
                            "4. Execute this script again with: --token VALUE_OF_THE_SESSION_COOKIE")

        self.session_token = session_token
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "https://github.com/nmrazvan/vaccinare-covid-api"
        }
        self.delay_between_requests = delay_between_requests
        self.last_request_at = None

    def _request(self, method, path, data=None):
        if self.last_request_at:
            time_since_last_request = datetime.now() - self.last_request_at
            wait_time = self.delay_between_requests - time_since_last_request.total_seconds()
            if wait_time > 0:
                time.sleep(wait_time)

        response = requests.request(
            method,
            API_URL + path,
            data=json.dumps(data) if data else None,
            headers=self.headers,
            cookies={"SESSION": self.session_token})

        self.last_request_at = datetime.now()
        return json.loads(response.text)

    def _get(self, path: str):
        return self._request("GET", path)

    def _post(self, path: str, data: dict):
        return self._request("POST", path, data)

    def get_counties(self):
        return self._get(COUNTIES_ENDPOINT)

    def get_centres(self, county_id=None, page=0, page_size=1000, recursive=True):
        while True:
            centres = self._post(
                f"{CENTRES_ENDPOINT}?page={page}&size={page_size}&sort=countyName,localityName,name",
                {"countyID": county_id, "localityID": None, "name": None})

            for centre in centres["content"]:
                yield centre

            if not recursive or centres["last"]:
                break

            page += 1

    def get_day_slots(self, centre_id, current_date):
        return self._post(DAY_SLOTS_ENDPOINT, {
            "centerID": centre_id,
            "currentDate": current_date,
            "forBooster": False})

    def get_available_slots(self, centre_id, months_to_check=2):
        for month in range(0, months_to_check):
            current_date = datetime.now() + relativedelta(months=month)
            days_available = self._post(MONTHLY_AVAILABILITY_ENDPOINT,
                                        data={"centerID": centre_id,
                                             "currentDate": current_date.strftime(DATE_FORMAT),
                                             "forBooster": False})
            for day in days_available:
                if day["availablePlaces"] > 0:
                    for slot in self.get_day_slots(centre_id, day["startTime"]):
                        if slot["availablePlaces"] > 0:
                            slot["startTime"] = datetime.strptime(slot["startTime"], DATE_FORMAT)
                            slot["endTime"] = datetime.strptime(slot["endTime"], DATE_FORMAT)
                            yield slot

    def get_available_slots_for_all_centres(self, months_to_check=2):
        for centre in self.get_centres():
            for slot in self.get_available_slots(centre["id"]):
                yield centre, slot


class CsvWriter:
    def __init__(self, file, header=None):
        self.file = file
        self.writer = csv.writer(file)
        self.header = header if header else {
            "centre.countyName": "Județ",
            "centre.localityName": "Localitate",
            "centre.name": "Centru",
            "centre.address": "Adresă centru",
            "misc.dates": "Date disponibile"
        }
        self._current_record = None

    def start(self):
        self.writer.writerow(self.header.values())
        self.file.flush()

    def write(self, centre, slot):
        record = {
            "centre": centre,
            "slot": slot,
            "misc": {
                "dates": {slot["startTime"].date().strftime("%Y-%m-%d")}
            }
        }

        if self._current_record and self._current_record["centre"]["id"] != centre["id"]:
            self._flush_current_record()

        if not self._current_record:
            self._current_record = record

        self._current_record["misc"]["dates"].add(next(iter(record["misc"]["dates"])))

    def end(self):
        self._flush_current_record()

    def _flush_current_record(self):
        row = []
        for property_path, _ in self.header.items():
            obj, prop = property_path.split(".")
            val = self._current_record[obj][prop]
            if type(val) is set:
                val = ";".join(sorted(val))
            row.append(val)
        self.writer.writerow(row)
        self.file.flush()
        self._current_record = None
