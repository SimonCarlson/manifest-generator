#!/home/rzmd/anaconda3/bin/python
import json
import cbor
import argparse
import uuid
import hashlib
import os

def generate_json(args, file=None):
    json_data = {}
    if file is not None:
        with open(file, "r") as f:
            json_data["versionID"] = f["versionID"]
            json_data["conditions"] = []
            for (i, entry) in enumerate(f["conditions"]):
                json_data["conditions"][i] = entry
    
    if json_data["versionID"] is None:
        json_data["versionID"] = args["m"]
    json_data["sequenceNumber"] = timestamp
    json_data["format"] = get_format(args["i"])
    json_data["size"] = os.path.getsize(args["i"])
    present_conditions = []
    for entry in json_data["conditions"]:
        present_conditions.append(entry["type"])
    if 0 not in present_conditions:
        # generate UUID5 from vendor dns
        vendorID = "a"
        json_data["conditions"].append({"type":0,"UUID":vendorID})
    if 1 not in present_conditions:
        # generate UUID5 from vendorID, get from previous or manifest
        classID = "b"
        json_data["conditions"].append({"type":1,"UUID":classID})
    if 2 not in present_conditions and args["d"] is not None:
        # generate UUID5 from classID
        deviceID = "c"
        json_data["conditions"].append({"type":2,"UUID":deviceID})

    json_data["digests"] = []
    json_data["digests"].append({"URI":args["u"],"digest":hashlib.sha256(args["i"])})
    
    return json_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Create a manifest.")
    parser.add_argument("outfile", metavar="outfile", type=str)
    parser.add_argument("-f", metavar="infile", type=str, help="Derive manifest version, vendor, class, and device from this manifest.")
    parser.add_argument("-m", metavar="manifest version", type=int)
    parser.add_argument("-i", metavar="image file", type=str, default=None)
    parser.add_argument("-v", metavar="vendor", type=str)
    parser.add_argument("-c", metavar="class", type=str)
    parser.add_argument("-d", metavar="device", type=str)
    parser.add_argument("-u", metavar="URI", type=str)
    args = vars(parser.parse_args())

    json_data = generate_json(args, file=args["f"])
    cbor_data = cbor.dumps(json_data)

    outfile = args["outfile"]
    print(".cbor" not in outfile)
    if ".cbor" not in outfile:
        outfile = outfile + ".cbor"
    print(outfile)
    with open(outfile, "wb") as file:
        file.write(cbor_data)

    