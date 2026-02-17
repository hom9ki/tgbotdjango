from abc import ABC, abstractmethod


class FileProcessor(ABC):

    @abstractmethod
    def process(self, file_bytes: bytes, file_name: str) -> tuple:
        pass



