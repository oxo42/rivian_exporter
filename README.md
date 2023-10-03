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

Then add `VIN=<YourVin>` to the credentials file

#### Dump vehicle info
This calls the same function the prometheus exporter calls
```shell
docker run --env-file /tmp/rivian-creds -it rivian_exporter vehicle-state | jq
```

### Run the exporter for the final step, run the exporter
```shell
docker run -p 8000 --env-file /tmp/rivian-creds rivian_exporter prometheus
curl http://localhost:8000
```


### Using Docker Secrets
Instead of having all the tokens and VIN as environment variables, you can store each one in a file then use docker secrets to populate those files.  You need to specificy the environment variables
* `ACCESS_TOKEN_FILE` => `/run/secrets/access_token`
* `REFRESH_TOKEN_FILE` => `/run/secrets/refresh_token`
* `USER_SESSION_TOKEN_FILE` => `/run/secrets/user_session_token`
* `VIN_FILE` => `/run/secrets/vin`



## TODO
* Setup CI for docker and publish
* Add metrics into the collector
* Build a class that holds the Rivian object and reuses it for querying the API
  * I am assuming this will use the websocket and I can then change the scrape interval much lower
* Split `RivianCollector` into `RivianGauge` and `RivianInfo`
  * The `Info` collector needs to take things from multiple fields, e.g. version having `otaCurrentVersion` and `otaCurrentVersionGitHash`.  This is a prometheus thing that I want to lean into