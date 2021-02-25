import requests
import json
import time
from flask import Flask, render_template, Blueprint
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_restx import Resource, Api
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from flask_rq2 import RQ


class Config(object):
    RQ_REDIS_URL = "redis://:password@redis:6379/0"
    RQ_QUEUES = ["default"]


# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Set up the flask app
app = Flask(__name__, static_url_path="/static/")
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config.from_object(Config())

# Set up the API endpoints
data_blueprint = Blueprint("api", __name__)
api = Api(data_blueprint, version="1.0", title="Short data", doc="/doc")
app.register_blueprint(data_blueprint, url_prefix="/api")
data_namespace = api.namespace("data", description="GME short data")

# Set up the workers
rq = RQ(app)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@data_namespace.route("/etfs")
class get_data(Resource):
    def get(self):
        with open("gme_shorts/data/etfs.json", "r") as data:
            return json.loads(data.read())


@data_namespace.route("/<string:etf>")
@data_namespace.response(404, "ETF data not found")
@data_namespace.param("etf", "The ETF ticker symbol")
class get_etf(Resource):
    def get(self, etf):
        with open(f"gme_shorts/data/{etf}.json", "r") as data:
            return json.loads(data.read())


url = "https://services-dynarep.ddwa.finra.org/public/reporting/v2/data/group/OTCMarket/name/RegSHODaily"


def get_payload(symbol):
    startDate = datetime.utcnow() + relativedelta(months=-3)
    endDate = datetime.utcnow()
    return json.dumps(
        {
            "fields": [
                "reportingFacilityCode",
                "tradeReportDate",
                "securitiesInformationProcessorSymbolIdentifier",
                "shortParQuantity",
                "shortExemptParQuantity",
                "totalParQuantity",
                "marketCode",
            ],
            "dateRangeFilters": [
                {
                    "fieldName": "tradeReportDate",
                    "startDate": startDate.strftime("%Y-%m-%d"),
                    "endDate": endDate.strftime("%Y-%m-%d"),
                }
            ],
            "domainFilters": [],
            "compareFilters": [
                {
                    "fieldName": "securitiesInformationProcessorSymbolIdentifier",
                    "fieldValue": symbol,
                    "compareType": "EQUAL",
                }
            ],
            "orFilters": [],
            "aggregationFilter": None,
            "sortFields": ["-tradeReportDate"],
            "limit": 150,
            "offset": 0,
            "delimiter": None,
            "quoteValues": False,
        }
    )


headers = {
    "authority": "services-dynarep.ddwa.finra.org",
    "accept": "application/json, text/plain, */*",
    "dnt": "1",
    "x-xsrf-token": "c19d9090-ea4e-4c73-8e7c-2a676090a529",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
    "content-type": "application/json",
    "origin": "https://www.finra.org",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://www.finra.org/",
    "accept-language": "en-US,en;q=0.9",
    "cookie": "_ga=GA1.2.1709553716.1614147348; _gid=GA1.2.411984779.1614147348; __cfduid=d76d6e2163d0fe7502c8c28bc284e31501614147349; XSRF-TOKEN=c19d9090-ea4e-4c73-8e7c-2a676090a529; AppSession=419cd52e-f01d-417b-b021-a2fcdeb320dd; __cfruid=d3a957f9f6434b34c3ee6a3e489e0d81a1c5aad1-1614147349; __cfduid=d1fe6b8a967d82a62b576471a5cc854501614149194; XSRF-TOKEN=51f6713f-0164-46d0-9e67-73a7205d7c0f; AppSession=9bca44eb-b124-44e7-9403-caa932411ae9; __cfruid=eceeade6d919896fa2b253754734a211ec712c43-1614149468",
}


@rq.job
def get_shorts():
    logging.info("getting shorts")
    etf_list = None
    with open("gme_shorts/etfs", "r") as etfs:
        etf_list = etfs.read().splitlines()
    with open("gme_shorts/data/etfs.json", "w") as data:
        data.write(json.dumps(etf_list))
    for etf in etf_list:
        time.sleep(1)
        with open(f"gme_shorts/data/{etf}.json", "w") as data:
            logging.info(f"Getting data for {etf}")
            response = requests.post(url, headers=headers, data=get_payload(etf))
            if response.ok:
                logging.info(f"Writing data for {etf} {response.json()['status']}")
                json_data = {
                    "label": etf,
                    "data": json.loads(response.json()["returnBody"]["data"]),
                }
                data.write(json.dumps(json_data))
            else:
                logging.error(f"Skipping data for {etf} {response.json()['status']}")


get_shorts.cron("*/5 * * * *", "get_shorts")


def run_app():
    app.run()
