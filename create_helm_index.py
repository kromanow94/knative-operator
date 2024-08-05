import yaml
import requests
import hashlib
from datetime import datetime

urls = [
    "https://github.com/knative/operator/releases/download/knative-v1.14.5/knative-operator-v1.14.5.tgz",
    "https://github.com/knative/operator/releases/download/knative-v1.14.4/knative-operator-v1.14.4.tgz"
]

index = {'apiVersion': 'v1', 'entries': {}}

for url in urls:
    name_version = url.split('/')[-1].replace('.tgz', '')
    name, version = name_version.rsplit('-', 1)
    response = requests.get(url)
    digest = hashlib.sha256(response.content).hexdigest()

    if name not in index['entries']:
        index['entries'][name] = []

    index['entries'][name].append({
        'apiVersion': 'v2',
        'name': name,
        'version': version,
        'urls': [url],
        'created': datetime.utcnow().isoformat() + 'Z',
        'digest': digest
    })

with open('index.yaml', 'w') as f:
    yaml.dump(index, f, sort_keys=False)
