# coding=utf-8
import json

from scrapy.loader import ItemLoader


class JsonItemLoader(ItemLoader):
    def __init__(self, *args, **kwargs):
        super(JsonItemLoader, self).__init__(*args, **kwargs)
        self.json_data = json.loads(kwargs['response'].text)

    def add_json(self, field_name, path, *processors):
        values = self._get_json_values(path)
        self.add_value(field_name, values, *processors)

    # TODO: nested_json

    def _get_json_values(self, path):
        data = self.json_data
        for key in path.split('/'):
            if data is None:
                break
            data = data.get(key)
        return data
