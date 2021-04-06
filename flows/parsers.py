from rest_framework.parsers import JSONParser


class VendorJSONParser(JSONParser):
    media_type = "application/vnd.api+json"
