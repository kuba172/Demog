class DataStorageModel:
    _dataFrames = {}

    @classmethod
    def add(cls, key, data_frame):
        original_key = key
        i = 1
        while cls.is_exists(key):
            key = f"{original_key}{i}"
            i += 1

        cls._dataFrames[key] = data_frame

    @classmethod
    def get(cls, key):
        return cls._dataFrames.get(key, None)

    @classmethod
    def update(cls, key, new_data_frame):
        if key in cls._dataFrames:
            cls._dataFrames[key] = new_data_frame
            return True
        else:
            return False

    @classmethod
    def remove(cls, key):
        if key in cls._dataFrames:
            del cls._dataFrames[key]
            return True
        else:
            return False

    @classmethod
    def get_all_keys(cls):
        return list(cls._dataFrames.keys())

    @classmethod
    def is_exists(cls, key):
        if key in cls._dataFrames:
            return True
        else:
            return False

    @classmethod
    def copy(cls):
        return cls._dataFrames.copy()

    @classmethod
    def clear(cls):
        cls._dataFrames.clear()

    @classmethod
    def get_all_keys_for_the_same_districts(cls, prefix):
        prefix = prefix.rsplit(', rok', 1)[0]
        return [key for key in cls._dataFrames.keys() if key.startswith(prefix)]
