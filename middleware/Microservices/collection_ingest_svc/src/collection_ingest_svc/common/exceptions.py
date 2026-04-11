class CollectionNotFoundError(Exception):
    pass


class IngestAlreadyInProgressError(Exception):
    pass


class AirflowInvocationError(Exception):
    pass


class VectorDbConfigError(Exception):
    pass
