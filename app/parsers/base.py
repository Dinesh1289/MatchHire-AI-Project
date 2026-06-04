from abc import ABC, abstractmethod


class BaseResumeParser(ABC):

    @abstractmethod
    def parse(self, file_path: str):
        pass