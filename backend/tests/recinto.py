"""The error the suite fence raises. Outside conftest so the class stays one object even when
pytest runs twice in one process (mutmut does) and conftest is loaded again."""


class SuiteInRete(BaseException):
    """Una prova ha chiamato un servizio vero senza fingerlo (`dentro_il_recinto`)."""
