def extract_added_words(fileobj, keywords, comment_tags, options):
    def yielder(data):
        for value in data:
            yield (None, None, [value], [])

    encoding = "utf-8"
    data = fileobj.read().decode(encoding).splitlines()

    return yielder(data)
