#
# Copyright © European Union 2022
#
# Licensed under the EUPL, Version 1.2 or – as soon they will be approved by
# the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the Licence for the specific language governing permissions and limitations under the Licence.
#

######## imports ########
from threading import Thread, Lock
import ntplib
import time
from datetime import datetime


class NTPClient:
    def __init__(self, ntp_server: str):

        self.ntp_client = ntplib.NTPClient()
        self.ntp_server_name = ntp_server

        self.time_update_lock = Lock()
        self.last_ntp_time = None
        self.last_monotonic = None
        while True:
            try:
                self._query_ntp_time()  # initialize NTP and monotonic, small delay between them
            except ntplib.NTPException as e:
                print(f"Error with the NTP server: {e} Retrying in 5 seconds.")
                time.sleep(5)
            else:
                break
        self.ntp_query_thread = Thread(target=self._query_ntp_time_recurrent, daemon=True)
        self.ntp_query_thread.start()
        print(f"NTPClient initialized with the server {self.ntp_server_name}.")

    def _query_ntp_time(self):
        r = self.ntp_client.request(self.ntp_server_name, version=3)
        with self.time_update_lock:
            self.last_ntp_time = r.tx_time  # Actually server time, we could account for the network delay
            self.last_monotonic = time.monotonic()

    def _query_ntp_time_recurrent(self):
        while True:
            try:
                self._query_ntp_time()
            except ntplib.NTPException as e:
                print(f"Error with the NTP server update: {e} Will continue using monotonic clock.")
            time.sleep(60)

    def get_current_time(self):
        with self.time_update_lock:
            time_elapsed = time.monotonic() - self.last_monotonic
            current_time = self.last_ntp_time + time_elapsed
        return current_time


if __name__ == '__main__':
    ntp_client = NTPClient('pool.ntp.org')

    while True:
        current_time = ntp_client.get_current_time()
        print(datetime.utcfromtimestamp(current_time))
        time.sleep(5)


