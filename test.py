#!/home/rzmd/anaconda3/bin/python
import cbor
import json

with open("example-manifest.json","r") as file:
	data = file.read()
	j = json.loads(data)

with open("example-manifest.cbor","wb") as file:
	file.write(cbor.dumps(j))

