from .result import GoogleResult


def _execute_google(circuit, simulator, **kwargs):

    result = simulator.run(circuit, **kwargs)

    return GoogleResult(result)
