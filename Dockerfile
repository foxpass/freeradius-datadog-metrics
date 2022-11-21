FROM datadog/agent:latest-jmx

RUN apt-get update -y && apt-get install freeradius-utils -y --option=Dpkg::Options::=--force-confdef
COPY freeradius.py /etc/datadog-agent/checks.d/
#COPY freeradius.yaml /etc/datadog-agent/conf.d/freeradius.yaml # Not required for container metrics
