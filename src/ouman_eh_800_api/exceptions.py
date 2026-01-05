
class OumanClientError(Exception):
    pass

class OumanClientAuthenticationError(OumanClientError):
    pass

class OumanClientCommunicationError(OumanClientError):
    pass
