from abc import ABC, abstractmethod


class BaseProcessingFiles(ABC):

    def __init__(self, file_bytes: bytes, file_name: str):
        self.file_name = file_name
        self.file_bytes = file_bytes
        self._processed_data = None


    @abstractmethod
    def process(self) -> tuple[bytes, str]:
        """
            Обработка файла.
            Возвращает обработанный файл + имя файла.
        """
        pass

    def _get_processed(self):
        if self._processed_data is None:
            self._processed_data = self.process()
        return self._processed_data

    @property
    @abstractmethod
    def get_stream(self) -> bytes:
        """Возвращает поток байтов файла"""
        pass

    @property
    @abstractmethod
    def get_file_name(self) -> str:
        """Возвращает имя файла"""
        pass