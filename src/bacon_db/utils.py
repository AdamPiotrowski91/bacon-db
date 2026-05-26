import inspect as ins


def count_required_args(fn):
    """Count required arguments in a callable."""

    if not callable(fn):
        raise ValueError("`fn` needs to be a callable.")

    sig = ins.signature(fn)
    required = 0

    for p in sig.parameters.values():
        if p.kind in (ins.Parameter.VAR_POSITIONAL, ins.Parameter.VAR_KEYWORD):
            continue

        # parameters without a default are required
        if p.default is ins.Parameter.empty:
            required += 1

    return required
