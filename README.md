# BeerClub

A web application to keep track of the beer accounts for registered members.

## Development

The contribution model is to fork the main repository and submit pull requests.

To test changes, please deploy the website locally.

## Local Deployment

It's recommended to use conda to keep the installation environment clean.

First, create a new environment and install the dependencies:

```bash
conda create --name BeerClub --yes python=2.7.15
conda activate BeerClub
pip install -r requirements.txt
```

Next, make a new `settings.json` file based on the template:

```bash
cd beerclub
cp template_settings.json settings.json
```

The BeerClub site uses CouchDB to store data.
You can install this locally if you want, or use Docker:

```bash
docker run -p 5984:5984 -d couchdb
```

Once the docker image is running, go to  http://127.0.0.1:5984/_utils/#/setup
and add a user with a password. Then create a new database.
The `template_settings.json` file contains the following defaults
(obviously for local testing only!):

```json
"DATABASE_ACCOUNT": "admin",
"DATABASE_PASSWORD": "admin",
"DATABASE_SERVER": "http://0.0.0.0:5984/",
"DATABASE_NAME": "beerclub",
"DATABASE_PASSWORD": "beerclub",
```

The BeerClub site needs to have it's directory added to the `PYTHONPATH` to work,
so from the repository root directory run the following:

```bash
export PYTHONPATH=$PWD:$PYTHONPATH
```

Finally, run the tornado web server:

```bash
python app_beerclub.py
```

The BeerClub website should now be running at http://localhost:8888/
