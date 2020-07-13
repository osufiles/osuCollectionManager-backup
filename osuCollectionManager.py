import argparse

# -------------------------------arguments--------------------------------
parser = argparse.ArgumentParser()

parser.add_argument(
    "-f", "--file", type=str, required=True, help="path to your collection.db file"
)
parser.add_argument("-l", "--list", action="store_true")
parser.add_argument("-m", "--merge", type=str)
# ------------------------------------------------------------------------

# -------------------------------main-------------------------------------
def main():
    args = parser.parse_args()

    collectionManager = CollectionManager(args)

    MainCollection = Collection()
    MainCollection.read_collection(args.file)

    if args.list:
        collectionManager.list(MainCollection)

    if args.merge:
        MergeCollection = Collection()
        MergeCollection.read_collection(args.merge)

        collectionManager.merge_collections(MainCollection, MergeCollection)


# ------------------------------------------------------------------------

# ------------------------------db format---------------------------------
class osuDbReader:
    def __init__(self, filepath):
        self.file = open(filepath, "rb")

    def read_byte(self):
        return int.from_bytes(self.file.read(1), "little")

    def read_short(self):
        return int.from_bytes(self.file.read(2), "little")

    def read_int(self):
        return int.from_bytes(self.file.read(4), "little")

    def read_long(self):
        return int.from_bytes(self.file.read(8), "little")

    def read_boolean(self):
        if self.read_byte == 0:
            return False
        else:
            return True

    def read_uleb128(self):
        result = 0
        shift = 0
        while True:
            byte = int.from_bytes(self.file.read(1), byteorder="little")

            result |= (byte & 0x7F) << shift
            if byte & 0x80 == 0:
                break
            shift += 7
        return result

    def read_string(self):
        if self.read_byte() == 0x0B:
            lenght = self.read_uleb128()
            return self.file.read(lenght).decode("utf-8")


class osuDbWriter:
    def __init__(self, filepath):
        self.file = open(filepath, "wb")

    def write_int(self, integer):
        int_b = integer.to_bytes(4, "little")
        self.file.write(int_b)

    def get_uleb128(self, integer):
        result = 0
        shift = 0
        while True:
            byte = integer

            result |= (byte & 0x7F) << shift
            # Detect last byte:
            if byte & 0x80 == 0:
                break
            shift += 7
        return result.to_bytes(1, "little")

    def write_string(self, string):
        if not string:
            # If the string is empty, the string consists of just this byte
            return bytes([0x00])
        else:
            # Else, it starts with 0x0b
            result = bytes([0x0B])

            # Followed by the length of the string as an ULEB128
            result += self.get_uleb128(len(string))

            # Followed by the string in UTF-8
            result += string.encode("utf-8")
            self.file.write(result)


# ------------------------------------------------------------------------

# --------------------------Collection class------------------------------
class Collection:
    def __init__(self):

        self.version = None
        self.cols_count = None
        self.collections = []

    def check_collection(self):
        if self.cols_count == 0:
            print("Collection is empty!")
            exit()

    def read_collection(self, filepath):
        db = osuDbReader(filepath)

        self.version = db.read_int()
        self.cols_count = db.read_int()

        # checking if collection is empty
        self.check_collection()

        for i in range(self.cols_count):
            collection_name = db.read_string()
            maps_count = db.read_int()

            self.md5hashes = []

            for i in range(maps_count):
                hash = db.read_string()
                self.md5hashes.append(hash)

            collection = {
                "name": collection_name,
                "maps_count": maps_count,
                "hashes": self.md5hashes,
            }
            self.collections.append(collection)

    def write_collection(self, filepath):
        db = osuDbWriter(filepath)

        db.write_int(self.version)
        db.write_int(self.cols_count)

        for collection in self.collections:
            db.write_string(collection["name"])
            db.write_int(collection["maps_count"])

            for i in range(collection["maps_count"]):
                db.write_string(collection["hashes"][i])


# ------------------------------------------------------------------------

# ------------------------Collection Manager------------------------------
class CollectionManager:
    def __init__(self, args):

        self.songs_folder = None

    def list(self, collection):
        print("Version:", collection.version)
        print("Total collections:", collection.cols_count)
        for c in collection.collections:
            print(c["name"] + ":")
            for hash in c["hashes"]:
                print("    -{}".format(hash))

    def merge_collections(self, collection_to, collection_from):
        merged_collection = Collection()

        merged_collection.version = collection_to.version

        for c in collection_to.collections:
            merged_collection.collections.append(c)

        for c in collection_from.collections:
            merged_collection.collections.append(c)

        merged_collection.cols_count = len(merged_collection.collections)
        merged_collection.write_collection("merged_collection.db")


# ------------------------------------------------------------------------

if __name__ == "__main__":
    main()
