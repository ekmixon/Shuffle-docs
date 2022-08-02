import os
import hashlib
import requests
from algoliasearch.search_client import SearchClient
from algoliasearch.exceptions import RequestException

client = SearchClient.create(os.getenv("ALGOLIA_CLIENT"), os.getenv("ALGOLIA_SECRET"))
index = client.init_index("documentation")

basedir = "../docs"
validurls = []
for dirname in os.listdir(basedir):
    if "md" not in dirname:
        continue

    if ".swo" in dirname or ".swp" in dirname:
        continue

    to_upload = []
    filename = "".join(dirname.split(".")[:-1])
    fileread = f"{basedir}/{dirname}"

    #print("Reading %s" % dirname)
    with open(fileread, "r") as tmp:
        try:
            data = tmp.read().split("\n")
        except UnicodeDecodeError as e:
            print(f"Error loading {dirname}: {e}")
            continue

        wrappeditem = {}
        curitem = ""
        for item in data:
            if item.startswith("#"):
                if curitem and wrappeditem["title"] != "Table of contents":
                    if wrappeditem["ref_url"] not in validurls:
                        ret = requests.get(wrappeditem["ref_url"])
                        #print("RET: %d - %s" % (ret.status_code, wrappeditem["ref_url"]))
                        if ret.status_code != 200:
                            print("SKIPPING %s (doesn't exist)" % wrappeditem["ref_url"])
                            break
                        else:
                            validurls.append(wrappeditem["ref_url"])

                    to_upload.append(wrappeditem)

                # Priority based on title
                title = " ".join(item.split("# ")[1:]).strip()
                priority = 5 - sum(char == "#" for char in item)
                # Hash is used for prioritizing the search
                title_hash = hashlib.md5(f"{filename}_{title}".encode("utf-8")).hexdigest()
                wrappeditem = {
                    "filename": filename,
                    "title": title.strip(),
                    "data": "",
                    "url": f'https://shuffler.io/docs/{filename}#{title.replace(" ", "_").lower()}',
                    "urlpath": f'/docs/{filename}#{title.replace(" ", "_").lower()}',
                    "objectID": title_hash,
                    "priority": priority,
                    "ref_url": f"https://github.com/frikky/shuffle-docs/blob/master/docs/{filename}.md",
                }

                curitem = item
                continue

            if item:
                curitem += item+"\n"
                try:
                    wrappeditem["data"] += item
                except KeyError:
                    wrappeditem["data"] = item

    if to_upload:
        try:
            ret = index.save_objects(to_upload)
            print("%s: %d objects" % (filename, len(to_upload)))
        except RequestException as e:
            print("ERROR: %s: %d objects: %s" % (filename, len(to_upload), e))
