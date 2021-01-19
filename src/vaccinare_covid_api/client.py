#!/usr/bin/env python3
import hashlib
import json
import os
import requests
import time
import logging

from datetime import datetime
from dateutil.relativedelta import relativedelta

API_URL = "https://programare.vaccinare-covid.gov.ro"
WEB_LOGIN_URL = "https://programare.vaccinare-covid.gov.ro/login"
CENTRES_ENDPOINT = "/scheduling/api/centres"
MONTHLY_AVAILABILITY_ENDPOINT = "/scheduling/api/time_slots/month_available_places"
DAY_SLOTS_ENDPOINT = "/scheduling/api/time_slots/day_slots"
COUNTIES_ENDPOINT = "/nomenclatures/api/county"
DATE_FORMAT = "%d-%m-%Y %H:%M:%S.%f"


class HttpSession:
    def __init__(self, session_token=None, session_token_file=None, cache_lifetime=None, fallback_cache_lifetime=None,
                 cache_path=None, delay_between_requests=None, max_retries=0, delay_between_retries=None):
        self.session_token = session_token
        self.session_token_file = session_token_file
        self.cache_lifetime = cache_lifetime
        self.fallback_cache_lifetime = fallback_cache_lifetime
        self.cache_path = cache_path
        self.delay_between_requests = delay_between_requests
        self.max_retries = max_retries
        self.delay_between_retries = delay_between_retries
        self.last_request_at = None
        self.headers = {"accept": "application/json",
                        "content-type": "application/json",
                        "user-agent": "https://github.com/nmrazvan/vaccinare-covid-api"}

    def _get_session_token(self):
        """
        Gets the session token. This needs to be provided via env vars or file, since it cannot be retrieved based on
        username and password since the login form uses captcha
        :return:
        """
        if self.session_token:
            return self.session_token

        if os.getenv("VACCINARE_TOKEN"):
            self.session_token = os.getenv("VACCINARE_TOKEN")
            return self.session_token

        if os.path.exists(self.session_token_file):
            with open(self.session_token_file, "r") as f:
                self.session_token = f.read().strip()
                return self.session_token

        raise Exception("No valid token found.\n"
                        "1. Go to https://programare.vaccinare-covid.gov.ro\n"
                        "2. Login\n"
                        "3. Get the value for the cookie called 'SESSION'\n"
                        "4. Run: export VACCINARE_TOKEN=VALUE_OF_THE_SESSION_COOKIE\n"
                        "5. Execute this script again")

    def _get_cache_file(self, method, path, data):
        cache_key = hashlib.md5(json.dumps([method, path, data]).encode()).hexdigest()
        return os.path.join(self.cache_path, cache_key)

    def _get_cache(self, method, path, data, lifetime):
        if not self.cache_path or lifetime is None:
            return
        cache_file = self._get_cache_file(method, path, data)
        if os.path.exists(cache_file):
            file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
            if file_age <= lifetime:
                with open(cache_file) as f:
                    return f.read()

    def _put_cache(self, method, path, data, response_body):
        if not self.cache_path or not (self.cache_lifetime or self.fallback_cache_lifetime):
            return
        cache_file = self._get_cache_file(method, path, data)
        if not os.path.exists(os.path.dirname(cache_file)):
            os.mkdir(os.path.dirname(cache_file))
        with open(cache_file, "w") as f:
            f.write(response_body)

    def request(self, method, path, data=None):
        logging.debug(f"{method} {path} {data}")

        response_body = self._get_cache(method, path, data, self.cache_lifetime)
        if response_body:
            logging.debug(f"Request is cached")
            return json.loads(response_body)

        if self.delay_between_requests and self.last_request_at:
            time_since_last_request = datetime.now() - self.last_request_at
            wait_time = self.delay_between_requests - time_since_last_request.total_seconds()
            if wait_time > 0:
                time.sleep(wait_time)

        retry_attempt = 0
        while retry_attempt <= self.max_retries:
            retry_attempt += 1
            response = requests.request(
                method,
                API_URL + path,
                data=json.dumps(data) if data else None,
                headers=self.headers,
                cookies={"SESSION": self._get_session_token()},
                allow_redirects=False)
            self.last_request_at = datetime.now()

            if response.headers.get("location") == WEB_LOGIN_URL:
                raise Exception("You need to retrieve the session token again")

            try:
                if response.status_code != 200:
                    raise Exception("Invalid response status code", response.status_code, response.text,
                                    response.headers)

                response_data = json.loads(response.text)
                self._put_cache(method, path, data, response.text)
                return response_data
            except Exception as e:
                if retry_attempt <= self.max_retries:
                    if self.delay_between_retries:
                        time.sleep(self.delay_between_retries)
                else:
                    response_body = self._get_cache(method, path, data, self.fallback_cache_lifetime)
                    if response_body is None:
                        raise Exception(f"{method} {path} failed after {retry_attempt} retries", e)
                    return json.loads(response_body)

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, data=None):
        return self.request("POST", path, data)


class VaccinareCovidApi:
    def __init__(self, session_token=None, session_token_file=None, cache_lifetime=None, fallback_cache_lifetime=None,
                 cache_path=None, delay_between_requests=None, max_retries=0, delay_between_retries=None):
        self.http = HttpSession(session_token=session_token,
                                session_token_file=session_token_file,
                                cache_lifetime=cache_lifetime,
                                fallback_cache_lifetime=fallback_cache_lifetime,
                                cache_path=cache_path,
                                delay_between_requests=delay_between_requests,
                                max_retries=max_retries,
                                delay_between_retries=delay_between_retries)

    def get_counties(self):
        return self.http.get(COUNTIES_ENDPOINT)

    def get_centres(self, county_id=None, page=0, page_size=1000, recursive=True):
        while True:
            centres = self.http.post(
                f"{CENTRES_ENDPOINT}?page={page}&size={page_size}&sort=countyName,localityName,name",
                {"countyID": county_id, "localityID": None, "name": None})

            for centre in centres["content"]:
                yield centre

            if not recursive or centres["last"]:
                break

            page += 1

    def get_day_slots(self, centre_id, current_date):
        return self.http.post(DAY_SLOTS_ENDPOINT, {
            "centerID": centre_id,
            "currentDate": current_date,
            "forBooster": False})

    def get_available_slots(self, centre_id, months_to_check=2):
        # Use a constant value for the time so that the request can be cached
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for month in range(0, months_to_check):
            current_date = now + relativedelta(months=month)
            days_available = self.http.post(MONTHLY_AVAILABILITY_ENDPOINT,
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
            for slot in self.get_available_slots(centre["id"], months_to_check):
                yield centre, slot
