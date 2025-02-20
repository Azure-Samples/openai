from abc import ABC, abstractmethod


class Flow(ABC):
    @abstractmethod
    def evaluate(self):
        '''
        Executes the evaluation flow
        '''
        pass