from hashlib import md5
import re
from subprocess import Popen, PIPE, STDOUT
import time

from checks import AgentCheck

DEFAULT_TIMEOUT = 1

STATISTICS_TYPES = {
    'authentication': 1,
    'accounting': 2,
    'proxy_authentication': 4,
    'proxy_accounting': 8
}


class TimeoutException(Exception):
    pass


class AccessRejectException(Exception):
    pass


class StatusCodeException(Exception):
    def __init__(self, status_code, output, *args, **kwargs):
        self.status_code = status_code
        self.output = output
        super(StatusCodeException, self).__init__(*args, **kwargs)


class FreeradiusCheck(AgentCheck):

    # retrieved from https://github.com/kshcherban/collectd-freeradius/blob/master/freeradius.py
    # (public GitHub repo without a license)
    REGEXP = re.compile('(FreeRADIUS-Total-.*) = (\d*)')

    def check(self, instance):
        # Check for required config parameters
        if 'host' not in instance:
            raise Exception("Missing 'host' from instance configuration")
        if 'port' not in instance:
            raise Exception("Missing 'port' from instance configuration")
        if 'secret' not in instance:
            raise Exception("Missing 'secret' from instance configuration")

        self.host = instance.get("host")
        self.port = instance.get("port")
        self.secret = instance.get("secret")
        self.timeout = float(instance.get('timeout', DEFAULT_TIMEOUT))
        self.tags = ["host:{}".format(self.host), "port:{}".format(self.port)]

        aggregation_inputs = "/".join([self.host, str(self.port)])
        self.aggregation_key = md5(aggregation_inputs).hexdigest()

        try:
            statistics_type = instance.get('type')
            if statistics_type is None:
                metrics = self.query_all()
            else:
                metrics = self.query(statistics_type)
        except TimeoutException:
            msg = "{}:{} failed to respond to status request. ".format(self.host, self.port) + \
                "FreeRADIUS may be down or the secret may be incorrect."
            self.report_error("No response from FreeRADIUS", msg)
            return
        except AccessRejectException:
            msg = "{}:{} rejected status request. FreeRADIUS may not be ".format(self.host, self.port) + \
                "configured to serve status requests or the secret may be incorrect."
            self.report_error("FreeRADIUS status request rejected", msg)
            return
        except StatusCodeException as e:
            msg = "radclient returned status code {} with this output: {}".format(
                e.status_code, e.output)
            self.report_error("radclient process returned error", msg)
            return {}

        for (metric, value) in metrics.items():
            if metric == 'freeradius.response_time':
                self.record_gauge(metric, value)
            else:
                self.record_monotonic_count(metric, value)

    def query_all(self):
        metrics = {}
        response_times = []
        for type in self.STATISTICS_TYPES.values():
            result = self.query(type)
            response_times.append(result.pop("freeradius.response_time"))
            metrics.update(result)
        metrics['freeradius.response_time'] = sum(response_times) / len(response_times)
        return metrics

    def query(self, statistics_type):
        cmd = ["radclient",
               "-t", str(self.timeout),
               "-x", "{}:{}".format(self.host, self.port),
               "status",
               self.secret]

        params = {"Message-Authenticator": "0x00",
                  "FreeRADIUS-Statistics-Type": statistics_type,
                  "Response-Packet-Type": "Access-Accept"}
        input = ", ".join(["{} = {}".format(k, v) for (k, v) in params.items()])

        proc = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        start_time = time.time()
        stdoutdata, stderrdata = proc.communicate(input=input)
        end_time = time.time()

        if "radclient: no response from server" in stdoutdata:
            raise TimeoutException()
        elif "rad_recv: Access-Reject" in stdoutdata:
            raise AccessRejectException()
        elif proc.returncode != 0:
            raise StatusCodeException(proc.returncode, stdoutdata)

        self.report_ok()

        metrics = self.REGEXP.findall(stdoutdata)
        metrics = dict([(self.format_metric(k), int(v)) for k, v in metrics])
        metrics['freeradius.response_time'] = end_time - start_time
        return metrics

    def format_metric(self, stat):
        return stat.lower().replace("-", ".").replace(".total.", ".")

    def record_gauge(self, metric, value):
        return self.gauge(metric, value, tags=self.tags)

    def record_monotonic_count(self, metric, value):
        return self.monotonic_count(metric, value, tags=self.tags)

    def report_ok(self):
        return self.service_check("freeradius", AgentCheck.OK, tags=self.tags)

    def report_error(self, msg_title, msg_text):
        self.service_check("freeradius", AgentCheck.CRITICAL, tags=self.tags, message=msg_title)
        return self.event({
            'timestamp': int(time.time()),
            'event_type': 'freeradius',
            'msg_title': msg_title,
            'tags': self.tags,
            'msg_text': msg_text,
            'aggregation_key': self.aggregation_key
        })
