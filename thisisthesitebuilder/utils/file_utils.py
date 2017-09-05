from checksumdir import dirhash


def get_hashes(DATA_DIR):
    data_hash = dirhash("{}/authored".format(DATA_DIR), 'md5')
    # app_hash = dirhash(PYTHON_APP_DIR, 'md5')
    hashes = {"data": data_hash}
              # "app": app_hash}

    return hashes