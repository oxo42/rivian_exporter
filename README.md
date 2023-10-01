# rivian_exporter

This is a prometheus_exporter that is scrapes data from the Rivian GraphAPI thanks to the [rivian-python-client](https://github.com/bretterer/rivian-python-client).

It is designed to be run as a docker image for the exporter daemon.  There are also CLI sub-commands to authenticate and fetch information about vehicles.  The intended flow is something like

![image](https://github.com/oxo42/rivian_exporter/assets/572079/2361ebc7-288d-4fb1-98ed-c5d8d00a3229)


## How to run

### Build

```shell 
docker build -t rivian_exporter .
```

### Login and save credentials

```shell
docker run -it rivian_exporter login
```

Save the last 3 lines to `/tmp/rivian-creds`

### Get user info

```shell
docker run --env-file /tmp/rivian-creds -it rivian user-info 
# add `| jq` to prettify it
```

#### Dump vehicle info
This calls the same function the prometheus exporter calls
```shell
docker run --env-file /tmp/rivian-creds -it rivian_exporter vehicle-state 7PDSGABA6PN022901 | jq
```

### Run the exporter for the final step, run the exporter
```shell
docker run -p 8000 --env-file /tmp/rivian-creds -e VIN="TheVin" rivian_exporter prometheus
curl http://localhost:8000
```

FWIW I put all the parameters as environment variables so they can easily be
injected into the container from whatever secrets tool you use (docker-compose,
kubernetes, etc)


## TODO
* Setup CI for docker and publish
* Add metrics into the collector
