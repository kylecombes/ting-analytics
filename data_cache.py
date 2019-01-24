from pathlib import Path


class DataCache:

    def __init__(self, cache_dir):
        """
        :param cache_dir: where to save downloaded files
        """
        self.cache_dir = Path(cache_dir) if (cache_dir and cache_dir is not Path) else cache_dir

    def fetch_if_necessary(self, filename, url, session, subdirectory=None):
        directory = (self.cache_dir / subdirectory) if subdirectory else self.cache_dir
        file_path = directory / filename

        if file_path.exists():
            return

        if directory.exists() and not directory.is_dir():
            raise FileExistsError('{} already exists but is not a directory.'.format(directory))

        if not directory.exists():
            print('Creating cache directory {}...'.format(directory))
            directory.mkdir(parents=True)

        self._download_file_to_disk(url, file_path, session)

    @staticmethod
    def _download_file_to_disk(url, output_path, session):
        if output_path.is_file():
            raise FileExistsError('File {} already exists.'.format(output_path))

        response = session.get(url, allow_redirects=True)
        open(str(output_path), 'wb').write(response.content)

