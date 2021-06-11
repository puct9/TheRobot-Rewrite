from copy import deepcopy
from typing import Any, Dict, List


class BaseDB:
    async def censor_list(self) -> List[str]:
        return []

    async def is_censor_exempt(self, user_id: int) -> bool:
        return False

    async def get_user(self, user_id: int) -> "UserBase":
        user = UserBase()
        user.id = str(user_id)
        return user


class BaseDataModel:
    _DEFAULT = {}

    def __init__(self) -> None:
        # Deepcopy required because mutable datatypes are allowed as values
        self._data: Dict[str, Any] = deepcopy(self._DEFAULT)

    def __getattribute__(self, name: str) -> Any:
        try:
            _data = super().__getattribute__("_data")
        except AttributeError:
            # Class has not yet been initialised; stay out of the way for now
            return super().__getattribute__(name)
        if name not in _data:
            try:
                # Fallback to finding method attribute
                return super().__getattribute__(name)
            except AttributeError:
                raise AttributeError(
                    f"Data model '{self.__class__.__name__}' has no attribute "
                    f"'{name}'"
                )
        return _data[name]

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_data":
            return super().__setattr__(name, value)
        if name not in self._DEFAULT:
            return super().__setattr__(name, value)
        expected_type = type(self._DEFAULT[name])
        if not isinstance(value, expected_type):
            raise TypeError(
                f"Data model attribute '{self.__class__.__name__}.{name}' "
                f"must be of type '{expected_type.__name__}' but got type "
                f"'{type(value)}'"
            )
        self._data[name] = value

    async def commit(self) -> None:
        pass


class UserBase(BaseDataModel):
    _DEFAULT = {
        "id": "0",
        "censor_exempt": False,
    }

    def __init__(self) -> None:
        super().__init__()
        self.id: str
        self.censor_exempt: bool
