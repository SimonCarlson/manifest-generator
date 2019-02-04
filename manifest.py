#!/home/rzmd/anaconda3/bin/python
import json
import cbor
import argparse
import uuid
import hashlib
import os
import time
import sys
import pathlib

format_mappings = {".bin":0, ".elf":1, ".tar":2}

def get_format(image_path):
    suffix = pathlib.Path(image_path).suffixes[0]
    return format_mappings[suffix]


def generate_json(args, file=None):
    json_data = {}
    if file is not None:
        with open(file, "r") as f:
            f = json.load(f)
            # Assume the version of manifest is the same since user wants to build upon manifest
            json_data["versionID"] = f["versionID"]
            conditions = []
            # Copy existing conditions as the manifest targets same device
            for entry in f["conditions"]:
                conditions.append(entry)
    
    if json_data["versionID"] is None:
        json_data["versionID"] = args["m"]

    timestamp = time.time()
    timestamp = str(timestamp).split(".")[0]
    json_data["sequenceNumber"] = timestamp

    json_data["format"] = get_format(args["i"])
    json_data["size"] = os.path.getsize(args["i"])

    json_data["conditions"] = conditions
    present_conditions = []
    for entry in json_data["conditions"]:
        present_conditions.append(entry["type"])
    if 0 not in present_conditions:
        # generate UUID5 from vendor dns
        vendorID = uuid.uuid5(uuid.NAMESPACE_DNS, "test.com")
        json_data["conditions"].append({"type":0,"UUID":vendorID})
    elif 0 in present_conditions:
        # Convert it to UUID so that it can be used as namespace for other UUIDs
        vendorID = uuid.UUID(json_data["conditions"][0]["UUID"])

    if 1 not in present_conditions:
        # generate UUID5 from vendorID, get from previous or manifest
        classID = uuid.uuid5(vendorID, "class1")
        json_data["conditions"].append({"type":1,"UUID":classID})
    elif 1 in present_conditions:
        classID = uuid.UUID(json_data["conditions"][1]["UUID"])

    if 2 not in present_conditions and args["d"] is not None:
        # generate UUID5 from classID
        deviceID = uuid.uuid5(classID, "device1")
        json_data["conditions"].append({"type":2,"UUID":deviceID})

    json_data["digests"] = []
    with open(args["i"], "rb") as f:
        data = f.read()
        image_digest = hashlib.sha256(data).hexdigest()
    json_data["digests"].append({"URI":args["u"],"digest":image_digest})
    
    return json_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create a manifest.")
    parser.add_argument("outfile", metavar="outfile", type=str)
    parser.add_argument("-f", metavar="infile", type=str, help="Derive manifest version, vendor, class, and device from this manifest.")
    parser.add_argument("-m", metavar="manifest version", type=int)
    parser.add_argument("-i", metavar="image file", type=str)
    parser.add_argument("-v", metavar="vendor", type=str)
    parser.add_argument("-c", metavar="class", type=str)
    parser.add_argument("-d", metavar="device", type=str)
    parser.add_argument("-u", metavar="URI", type=str)
    args = vars(parser.parse_args())
    
    if args["f"] is None or not os.path.isfile(args["f"]):
        print("Could not find manifest.")
        sys.exit(1)
    elif pathlib.Path(args["f"]).suffix != ".json":
        print("Manifest must be a JSON file.")
        sys.exit(1)
    if args["i"] is None or not os.path.isfile(args["i"]):
        print("Could not find image.")
        sys.exit(1)
    

    json_data = generate_json(args, file=args["f"])
    cbor_data = cbor.dumps(json_data)

    outfile = pathlib.Path(args["outfile"]).stem
    with open(outfile + ".json", "w") as file:
        json.dump(json_data, file)
        print("Wrote JSON manifest to {}.json.".format(outfile))
    with open(outfile + ".cbor", "wb") as file:
        file.write(cbor_data)
        print("Wrote CBOR manifest to {}.cbor.".format(outfile))

    