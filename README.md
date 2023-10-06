# rivian_exporter

WARNING: This is still a work in progress.  Come find me on the [Rivian Discord](https://discord.gg/JjQjSxv3ND) in the [`#tech-software`](https://discord.com/channels/892997443896111105/997683089667018762) channel if you have issues.

This is a prometheus_exporter that is scrapes data from the Rivian GraphAPI thanks to the [rivian-python-client](https://github.com/bretterer/rivian-python-client).

It is designed to be run as a docker image for the exporter daemon.  There are also CLI sub-commands to authenticate and fetch information about vehicles.  The intended flow is something like

![image](https://github.com/oxo42/rivian_exporter/assets/572079/2361ebc7-288d-4fb1-98ed-c5d8d00a3229)

You can get [my dashboard from Grafana](https://grafana.com/grafana/dashboards/19692-rivian/).  Warning, I'm odd and use miles for distance and celsius for temperature.  If you build your own dash, pull request to link it here.

## How to run

The image is published to [`ghcr.io/oxo42/rivian_exporter:latest`](https://github.com/oxo42/rivian_exporter/pkgs/container/rivian_exporter)

### Build

```shell 
docker build -t ghcr.io/oxo42/rivian_exporter .
```

### Login and save credentials

```shell
docker run -it ghcr.io/oxo42/rivian_exporter login
```

Save the last 3 lines to `/tmp/rivian-creds`

### Get user info

```shell
docker run --env-file /tmp/rivian-creds -it ghcr.io/oxo42/rivian_exporter user-info 
# add `| jq` to prettify it
```

Then add `VIN=<YourVin>` to the credentials file

#### Dump vehicle info
This calls the same function the prometheus exporter calls
```shell
docker run --env-file /tmp/rivian-creds -it ghcr.io/oxo42/rivian_exporter vehicle-state | jq
```

### Run the exporter for the final step, run the exporter
```shell
docker run -p 8000 --env-file /tmp/rivian-creds ghcr.io/oxo42/rivian_exporter
curl http://localhost:8000
```


### Using Docker Secrets
Instead of having all the tokens and VIN as environment variables, you can store each one in a file then use docker secrets to populate those files.  You need to specificy the environment variables
* `ACCESS_TOKEN_FILE` => `/run/secrets/access_token`
* `REFRESH_TOKEN_FILE` => `/run/secrets/refresh_token`
* `USER_SESSION_TOKEN_FILE` => `/run/secrets/user_session_token`
* `VIN_FILE` => `/run/secrets/vin`



## TODO
* Add metrics into the collector
* Split `RivianCollector` into `RivianGauge` and `RivianInfo`
  * The `Info` collector needs to take things from multiple fields, e.g. version having `otaCurrentVersion` and `otaCurrentVersionGitHash`.  This is a prometheus thing that I want to lean into
* Add a `get-vehicles` CLI to help with setup


# Dev notes

Run the app with
```shell
poetry run python -m rivian_exporter --help
# or
bin/rivian_exporter --help
```

Tests
```shell
poetry run pytest
```