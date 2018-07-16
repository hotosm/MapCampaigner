"""Apache Bench for server side profiling.
To run the file use cmd: { python3 profiling-ab.py param1 param2 }
:param1: number of requests to the application's URLs.
:param2: maximum time limit to execute the requests.
:return: terminal logs including applications statistics.
"""

import os
import sys
import subprocess

from sqlaclhemy.orm import sessionmaker

from campaign_manager.models.models import Campaign


request_number = sys.argv[1]  # param1
time_limit = sys.argv[2]  # param2

ab_cmd = "ab " + "-n " + request_number + " " + "-t " + time_limit


class ProfileUrls():
    """Profile individual URL's"""

    def request_all(self):
        cmd = ab_cmd + " " + "http://localhost:5000/all"
        subprocess.call(cmd, shell=True)

    def request_detail(self, uuid):
        cmd = ab_cmd + " " + "http://localhost:5000/campaign/" + uuid
        subproccess.call(cmd, shell=True)


profiler = ProfileUrls()
profiler.request_all()

try:
    campaign = Campaign().get_first()
except Exception as e:
    print(e)

profiler.request_detail(campaign.uuid)
