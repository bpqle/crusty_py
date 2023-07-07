def pub_err(comp):
    raise ConnectionError(f"Did not receive confirmation for component {comp}")


def rep_err(msg=None, comp=None, e=None):
    if e is not None:
        if msg is None:
            raise e(f"Error awaiting reply from decide-rs, component {comp}")
        else:
            raise e(f"{msg}, component {comp}")
    else:
        if msg is None:
            raise f"Error awaiting reply from decide-rs, component {comp}"
        else:
            raise f"{msg}, component {comp}"
