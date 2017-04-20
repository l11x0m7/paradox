from enum import Enum
from abc import abstractmethod
from paradox.kernel import *
from paradox.utils import generate_label_matrix


class LossCategory(Enum):
    LossCategory = 0
    classification = 1
    regression = 2


class LossLayer:
    loss_type = None

    @abstractmethod
    def loss_function(self, *args, **kwargs):
        pass


class SoftMaxLoss(LossLayer):
    loss_type = LossCategory.classification

    @staticmethod
    def loss_function(input_symbol: Symbol, label_matrix, get_label_symbol: bool=False):
        label_symbol = Symbol(label_matrix)
        exp_symbol = exp(input_symbol)
        softmax_value = reduce_sum(label_symbol * exp_symbol, axis=1) / reduce_sum(exp_symbol, axis=1)
        loss = reduce_mean(-log(softmax_value))
        if get_label_symbol:
            return loss, label_symbol
        else:
            return loss


class SVMLoss(LossLayer):
    loss_type = LossCategory.classification

    @staticmethod
    def loss_function(input_symbol: Symbol, label_matrix, get_label_symbol: bool=False):
        dimension = label_matrix.shape[0]
        label_matrix *= -(dimension - 1)
        label_matrix[label_matrix == 0] = 1
        label_symbol = Symbol(label_matrix)
        loss = reduce_mean(maximum(reduce_sum(label_symbol * input_symbol, axis=1) + (dimension - 1), 1))
        if get_label_symbol:
            return loss, label_symbol
        else:
            return loss


softmax_loss = SoftMaxLoss.loss_function
svm_loss = SVMLoss.loss_function


def softmax_loss_with_label(input_symbol: Symbol, classification, get_label_symbol: bool=False):
    class_matrix = generate_label_matrix(classification)[0]
    return softmax_loss(input_symbol, class_matrix, get_label_symbol)


def svm_loss_with_label(input_symbol: Symbol, classification, get_label_symbol: bool=False):
    class_matrix = generate_label_matrix(classification)[0]
    return svm_loss(input_symbol, class_matrix, get_label_symbol)


loss_map = {
    'softmax': SoftMaxLoss,
    'svm': SVMLoss,
}


def register_loss(name: str, loss: LossLayer):
    loss_map[name.lower()] = loss


class Loss:
    def __init__(self, name: str, *args, **kwargs):
        self.__name = name.lower()
        self.__loss = None
        if self.__name in loss_map:
            self.__loss = loss_map[self.__name](*args, **kwargs)
        else:
            raise ValueError('No such loss: {}'.format(name))

    def loss_layer(self):
        return self.__loss
