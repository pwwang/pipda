"""Provide the Operator class"""
import operator
from typing import Any, Callable, Mapping, Optional, Tuple, Type, Union

from .utils import Context, Predicate, evaluate_args, evaluate_kwargs

class Operator(Predicate):
    """Operator class, defining how the operators in verb/function arguments
    should be evaluated

    Args:
        op: The operator
        args: The arguments of the operator
        kwargs: The keyword arguments of the operator
    """
    REGISTERED = None

    def __init__(self,
                 op: str,
                 args: Tuple[Any],
                 kwargs: Mapping[str, Any]) -> None:
        self.op = op
        op_func = getattr(self, self.op)

        context = self.__class__.context
        if isinstance(context, dict):
            context = context.get(self.op, Context.DATA)
        super().__init__(op_func, context)

        self.defer(args, kwargs)
        self.data = None

    def evaluate(self, data: Any, context: Context = Context.UNSET) -> Any:
        """Evaluate the operator

        No data passed to the operator function. It should be used to evaluate
        the arguments.
        """
        self.data = data
        if self.context == Context.UNSET:
            self.context = context

        args = evaluate_args(self.args, data, self.context)
        kwargs = evaluate_kwargs(self.kwargs, data, self.context)
        return self.func(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        op_func = getattr(operator, name, None)
        if not op_func and name.startswith('r'):
            op_func = getattr(operator, name[1:], None)
            if op_func:
                return lambda a, b, *args, **kwargs: op_func(
                    b, a, *args, **kwargs
                )
        if op_func is None:
            raise ValueError(f'Cannot find the operator {name!r}, '
                             'have you define it in your operator class?')
        return op_func

def register_operator(
        op_class: Optional[Type[Operator]] = None,
        context: Union[Context, Mapping[str, Context]] = Context.MIXED
) -> Union[Type[Operator], Callable[[Type[Operator]], Type[Operator]]]:
    """Register an Operator class

    The context count be a dict of operator name to context.
    For those operators not listed, will use Context.DATA.
    """
    if not op_class:
        return lambda opc: register_operator(opc, context=context)

    if context == Context.MIXED:
        context = {
            'neg': Context.UNSET,
            'pos': Context.UNSET,
            'invert': Context.UNSET
        }

    if not issubclass(op_class, Operator):
        raise ValueError(
            "The operator class to be registered must be "
            "a subclass of pipda.Operator."
        )
    Operator.REGISTERED = op_class
    op_class.context = context
    return op_class

register_operator(Operator)
