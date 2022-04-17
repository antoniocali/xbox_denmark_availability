import requests
from dataclasses import dataclass
from typing import Dict, List, Callable, Union, Optional
from telethon import TelegramClient
from apscheduler.schedulers.blocking import BlockingScheduler
from config import settings
from enum import IntEnum
import signal


class Request(IntEnum):
    GET = 0
    POST = 1


api_id = settings["API_ID"]
api_hash = settings["API_HASH"]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
    "Accept": "application/json"
}
scheduler = BlockingScheduler()


@dataclass
class Result:
    url: str
    count: int


@dataclass
class Model:
    hostname: str
    api_url: str
    request: Request
    body: Optional[str]
    fun: Callable[[Union[Dict, List]], Result]


def get_product_v1(j: List) -> Result:
    doc = j[0]
    counts = doc["ClickNCollectStoreCount"] + doc["StockCount"]
    url = doc["Url"]
    return Result(url=url, count=counts)


def get_product_v2(j: Dict) -> Result:
    doc = j["doc"]
    counts = doc["stock_count_online"] + doc["in_stock_stores_count"]
    url = doc["product_url"]
    return Result(url=url, count=counts)


def get_product_v3(j: Dict) -> Result:
    doc = j["data"]["product"]
    counts = doc["availableForCollectAtStoreCount"] + int(doc["buyableInternet"]) + int(doc["buyableOnline"])
    url = doc["productURL"]
    return Result(url=url, count=counts)


urls: List[Model] = [
    Model(hostname="https://www.power.dk",
          api_url="https://www.power.dk/umbraco/api/product/getproductsbyids?ids=1119853",
          fun=get_product_v1,
          body=None, request=Request.GET),
    Model(hostname="https://www.expert.dk",
          api_url="https://www.expert.dk/umbraco/api/product/getproductsbyids?ids=1119853",
          fun=get_product_v1, body=None, request=Request.GET),
    Model(hostname="https://www.bilka.dk",
          api_url="https://api.sallinggroup.com/v1/ecommerce/bilka/search/pdp?id=200143235&apiKey=d889a569-6548-4a11-b447-c653730f1747",
          fun=get_product_v2, body=None, request=Request.GET),
    Model(hostname="https://www.foetex.dk",
          api_url="https://api.sallinggroup.com/v1/ecommerce/foetex/search/pdp?id=200143235&apiKey=4d73a371-3293-4875-9421-d65d45a2fdf1",
          fun=get_product_v2, body=None, request=Request.GET),
    Model(hostname="",
          api_url="https://www.elgiganten.dk/cxorchestrator/dk/api?appMode=b2c&user=anonymous&operationName=getProductWithDetails",
          body="{product(articleNumber:316328){availableForCollectAtStoreCount,productURL,buyableOnline,buyableInternet}}",
          request=Request.POST, fun=get_product_v3)
]


def main():
    print("Calling")
    for api in urls:
        req = requests.get(api.api_url, headers=headers) if api.request == Request.GET \
            else requests.post(api.api_url,
                               headers=headers,
                               json={
                                   'query': api.body})
        result = api.fun(req.json())
        if result.count > 0:
            with TelegramClient('anon', api_id, api_hash) as client:
                client.loop.run_until_complete(
                    client.send_message('me', f"Found {result.count} at {api.hostname}{result.url}"))


def signal_handler(sig, frame):
    print('Stopping!')
    scheduler.pause()
    scheduler.shutdown()


signal.signal(signal.SIGINT, signal_handler)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
    scheduler.add_job(main, 'interval', seconds=30)
    scheduler.start()
