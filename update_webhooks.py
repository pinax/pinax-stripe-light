import requests


URL = "https://stripe.com/docs/api/curl/sections?all_sections=1&version=2019-02-19&cacheControlVersion=4"
response = requests.get(URL)

data = response.json()

event_types = data["event_types"]["data"]["event_types"]

class_template = """class {class_name}Webhook(Webhook):
    name = "{name}"
    description = "{description}"


"""

header = """from .base import Webhook


"""

with open("pinax/stripe/webhooks/generated.py", "wb") as fp:
    fp.write(header.encode("utf-8"))
    for index, event_type in enumerate(event_types):
        name = event_type["type"]
        description = event_type["description"].replace('"', "'")
        class_name = name.replace(".", " ").replace("_", " ").title().replace(" ", "")

        code = class_template.format(
            class_name=class_name,
            name=name,
            description=description
        )
        if index + 1 == len(event_types):
            code = f"{code.strip()}\n"

        fp.write(code.encode("utf-8"))

        print(f"{name} added...")
    fp.close()
