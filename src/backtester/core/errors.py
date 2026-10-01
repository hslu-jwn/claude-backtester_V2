class LookaheadError(IndexError):
    """Raised when code tries to read a candle that has not closed yet at the current
    simulation cursor. This is a bug, never something to catch and ignore."""
