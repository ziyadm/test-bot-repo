import pyairtable


class AirtableClient:

    def __init__(self,
                 api_key: str,
                 base_id: str):
                     self.api_key = api_key
                     self.base_id = base_id

    def table(self,
              table_name: str):
                  return pyairtable.Table(api_key = self.api_key,
                                          base_id = self.base_id,
                                          table_name = table_name)