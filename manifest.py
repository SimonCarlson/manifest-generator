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
    conditions = []
    if file is not None:
        with open(file, "r") as f:
            f = json.load(f)
            # Assume the version of manifest is the same since user wants to build upon manifest
            json_data["versionID"] = f["versionID"]
            # Copy existing conditions as the manifest targets same device
            for entry in f["conditions"]:
                conditions.append(entry)
    
    if file is None:
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
        # If there is no vendor ID currently, make one
        vendorID = uuid.uuid5(uuid.NAMESPACE_DNS, args["v"])
        json_data["conditions"].append({"type":0,"UUID":str(vendorID)})
    elif 0 in present_conditions:
        # Convert string to UUID so that it can be used as namespace for other UUIDs
        vendorID = uuid.UUID(json_data["conditions"][0]["UUID"])

    if 1 not in present_conditions:
        classID = uuid.uuid5(vendorID, args["c"])
        json_data["conditions"].append({"type":1,"UUID":str(classID)})
    elif 1 in present_conditions:
        classID = uuid.UUID(json_data["conditions"][1]["UUID"])
        
    if 2 not in present_conditions and args["d"] is not None:
        deviceID = uuid.uuid5(classID, args["d"])
        json_data["conditions"].append({"type":2,"UUID":str(deviceID)})

    json_data["digests"] = []
    with open(args["i"], "rb") as f:
        data = f.read()
        image_digest = hashlib.sha256(data).hexdigest()
    json_data["digests"].append({"URI":args["u"],"digest":image_digest})
    
    return json_data

def validate_input(args):
    if args["f"] is not None and not os.path.isfile(args["f"]):
        print("Could not find manifest.")
        sys.exit(1)
    elif args["f"] is not None and pathlib.Path(args["f"]).suffix != ".json":
        print("Manifest must be a JSON file.")
        sys.exit(1)

    if args["i"] is None:
        print("Image file is needed.")
        sys.exit(1)
    elif not os.path.isfile(args["i"]):
        print("Could not find image file.")
        sys.exit(1)

    if args["f"] is None:
        if args["v"] is None:
            print("Vendor namespace is needed for vendor ID.")
            sys.exit(1)
        if args["c"] is None:
            print("Class identifier is needed for class ID.")
            sys.exit(1)
        if args["m"] is None:
            print("Manifest version is needed")
            sys.exit(1)

    if args["u"] is None:
        print("URI for the image is needed.")
        sys.exit(1)

def validate_manifest(filepath):
    with open(filepath, "r") as f:
        try:
            data = json.load(f)
        except json.decoder.JSONDecodeError:
            print("Manifest contains malformed JSON.")
            sys.exit(1)

        try:
            data["versionID"]
        except KeyError:
            print("Manifest is missing manifest version.")
            sys.exit(1)

        try:
            data["conditions"]
        except KeyError:
            print("Manifest is missing vendor and class IDs.")
            sys.exit(1)

        conditions = data["conditions"]
        present_types = []
        for condition in conditions:
            present_types.append(condition["type"])

        if 0 not in present_types:
            print("Manifest is missing vendor ID.")
            sys.exit(1)
        elif 0 in present_types:
            try:
                uuid.UUID(data["conditions"][0]["UUID"])
            except ValueError:
                print("Manifest is missing vendor ID.")
                sys.exit(1)

        if 1 not in present_types:
            print("Manifest is missing class ID.")
            sys.exit(1)
        elif 1 in present_types:
            try:
                uuid.UUID(data["conditions"][1]["UUID"])
            except ValueError:
                print("Manifest is missing class ID.")
                sys.exit(1)


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
    
    validate_input(args)
    if args["f"] is not None:
        validate_manifest(args["f"])

    json_data = generate_json(args, file=args["f"])
    cbor_data = cbor.dumps(json_data)

    outfile = pathlib.Path(args["outfile"]).stem
    with open(outfile + ".json", "w") as file:
        json.dump(json_data, file)
        print("Wrote JSON manifest to {}.json.".format(outfile))
    with open(outfile + ".cbor", "wb") as file:
        file.write(cbor_data)
        print("Wrote CBOR manifest to {}.cbor.".format(outfile))

    