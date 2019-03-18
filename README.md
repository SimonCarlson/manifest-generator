A manifest generator.

## Usage

The name of the outfile is always needed, as well as the -i and -u flags for image file and URI. 

An existing manifest can be specified via the -f flag. This will copy the manifest
version, vendor ID, and class ID to the new manifest. If no existing manifest is
specified, these values need to be added through the -m, -v, and -c flags.

In either case the generator calculates the size and checksum of the given image, creates
a monotonically increasing sequence number and structures the manifest accordingly. The
output is encoded as json and cbor for diagnostic purposes.