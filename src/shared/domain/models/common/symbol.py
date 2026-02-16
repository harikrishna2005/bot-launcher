from typing import Any
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class Symbol(str):
    """
    A smart Symbol object that self-cleans and splits Base/Quote.
    """

    def __new__(cls, value: str):
        # 1. Basic validation
        if not isinstance(value, str):
            raise TypeError("Symbol must be a string")

        # 2. Normalization logic
        normalized = value.strip().replace("_", "/").replace("-", "/").upper()

        # 3. Create the string object
        return super().__new__(cls, normalized)

    @property
    def base(self) -> str:
        return self.split("/")[0]

    @property
    def quote(self) -> str:
        return self.split("/")[1]

    def with_separator(self, sep: str = "/") -> str:
        return f"{self.base}{sep}{self.quote}"

    @classmethod
    def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Tells Pydantic to treat this as a string, but then run
        the Symbol() constructor on it to trigger our __new__ logic.
        """
        return core_schema.no_info_after_validator_function(
            cls,  # The function to run (our constructor)
            core_schema.str_schema()  # The expected input type
        )