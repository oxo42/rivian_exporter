# rivian_exporter

This is a prometheus_exporter that is scrapes data from the Rivian GraphAPI thanks to the [rivian-python-client](https://github.com/bretterer/rivian-python-client).

It is designed to be run as a docker image for the exporter daemon.  There are also CLI sub-commands to authenticate and fetch information about vehicles.  The intended flow is something like


```shell
$ docker run -it rivian_exporter login
```
```text
Username: me@example.com
Password: hunter2
Logging in with password
OTP Required
OTP: 12345
Validating OTP
ACCESS_TOKEN="SECRET"
REFRESH_TOKEN="ASO_SECRET"
USER_SESSION_TOKEN="OMG_ANOTHER_SECRET"
```

The other sub-commands expect those tokens to be part of the environment
```shell
docker run \
    -e ACCESS_TOKEN="SECRET" \
    -e REFRESH_TOKEN="ASO_SECRET" \
    -e USER_SESSION_TOKEN="OMG_ANOTHER_SECRET" \
    -it rivian_exporter list-vehicles
```
```plain
RIVIAN R1S: TheVin
RIVIAN R1T (TruckName): TheVin2
```

Then for the final step, run the exporter
```shell
docker run \
    -e ACCESS_TOKEN="SECRET" \
    -e REFRESH_TOKEN="ASO_SECRET" \
    -e USER_SESSION_TOKEN="OMG_ANOTHER_SECRET" \
    -e VIN="TheVin" \
    -it rivian_exporter prometheus
```