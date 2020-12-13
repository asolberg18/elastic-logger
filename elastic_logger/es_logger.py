import os
import aiohttp


class ElasticLogger:

    def __init__(self, schema, host=None, index=None, user=None, pw=None):
        self.schema = schema
        self.host = host or os.getenv("ELASTIC_HOST")
        self.index = index or os.getenv("ELASTIC_INDEX")
        self.index_uri = "{}/{}".format(self.host, self.index)
        self.session = aiohttp.ClientSession(auth=aiohttp.BasicAuth(
            login=user or os.getenv("ELASTIC_USERID"),
            password=pw or os.getenv("ELASTIC_PASSWORD"), encoding='utf-8'))

    async def __call__(self, event, silent=False):
        if not silent:
            print("\033[1K\rPosting event to {}".format(self.index))
        resp = await self.session.post("{}/_doc".format(self.index_uri), json=event)
        if resp.status != 201:
            print(event)
            print("\033[1K\rResponse: {}".format(resp.status))
            print(await resp.json())
        if not silent:
            print("\033[1K\rResponse: {}".format(resp.status))
            print(await resp.json())
        return resp

    async def close(self):
        await self.session.close()

    async def get_schema(self, silent=False):
        if not silent:
            print("\033[1K\rGetting schema of {}".format(self.index))
        resp = await self.session.get(self.index_uri)
        if not silent:
            print("\033[1K\rResponse: {}".format(resp.status))
            print(await resp.json())
        return resp

    async def init_schema(self, silent=False, deleteExisting=True):
        resp = await self.get_schema(silent=True)
        if resp.status == 200:
            if deleteExisting:
                if not silent:
                    print(
                        "\033[1K\rIndex {} exists, deleting.".format(self.index))
                await self.delete_index(silent=silent)
            else:
                if not silent:
                    print(
                        "\033[1K\rIndex {} exists, not deleting.".format(self.index))
                return False
        if not silent:
            print("\033[1K\rCreating {} schema".format(self.index))
        resp = await self.session.put(self.index_uri, json=self.schema)
        if not silent:
            print("\033[1K\rResponse: {}".format(resp.status))
            print(await resp.json())
        return resp

    async def delete_index(self, silent=False):
        if not silent:
            print("\033[1K\rDeleting index {}".format(self.index))
        resp = await self.session.delete(self.index_uri)
        if not silent:
            print("\033[1K\rResponse: {}".format(resp.status))
            print(await resp.json())
        return resp

    async def query(self, query, silent=False):
        if not silent:
            print("\033[1K\rExecuting query against {}".format(self.index))
        resp = await self.session.get("{}/_search".format(self.index_uri), json=query)
        if not silent:
            print("\033[1K\rResponse: {}".format(resp.status))
            print(await resp.json())
        return resp
