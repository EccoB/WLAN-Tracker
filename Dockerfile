FROM python:3
MAINTAINER Eiko Baeumker

RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" \
wireless-tools \
net-tools \
tshark \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*
RUN pip install paho-mqtt
RUN mkdir /sniffer
ADD sniffer.py /sniffer

CMD [ "python","/sniffer/sniffer.py"]
