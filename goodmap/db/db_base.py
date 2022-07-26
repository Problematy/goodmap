from abc import ABC, abstractmethod


class Database(ABC):

    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def save_entry(self, entry):
        pass
