A manifest generator. The generator calculates the size and checksum of the given image,
creates a monotonically increasing sequence number based on POSIX timestamps, generates
UUIDs for vendor and class IDs, and structures the manifest accordingly. The output is encoded as JSON and CBOR for diagnostic purposes. Developed on Python 3.7.1.

## Usage

### Parameters
The name of the outfile is always needed.

### Flags
-m: manifest version

-i: image file

-v: vendor namespace

-c: class namespace

-u: URI

-f: existing manifest to pull version, vendor and class namespaces from (no need for -m,
-v, -c flags) (optional)