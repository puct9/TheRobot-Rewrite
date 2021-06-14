from copy import deepcopy
from typing import Any, Callable, Dict, List


class BaseDB:
    def __init__(self, callback: Callable[[str, Any], None]) -> None:
        pass

    async def censor_list(self) -> List[str]:
        return []

    async def get_user(self, user_id: int) -> "UserBase":
        user = UserBase()
        user.id = str(user_id)
        return user

    async def quiz_subjects(self) -> List[str]:
        return []

    async def quiz_list(self, subject: str) -> List[str]:
        return []

    async def get_quiz(self, subject: str, name: str) -> "QuizBase":
        return QuizBase()


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


class QuizBase(BaseDataModel):
    # Demonstration of how quizzes can be laid out
    _DEFAULT = {
        "id": "",
        "question": "What is the capital of Australia?",
        "ordered": False,
        "required_correct": 1,
        "image": "",
        "options": [
            {
                "answer": "Canberra",
                "correct": True,
            },
            {
                "answer": "Melbourne",
                "correct": False,
            },
            {
                "answer": "Sydney",
                "correct": False,
            },
            {
                "answer": "Darwin",
                "correct": False,
            },
        ],
    }

    def __init__(self) -> None:
        super().__init__()
        self.id: str
        self.question: str
        self.ordered: bool
        self.required_correct: int
        self.image: str
        self.options: List[Dict[str, Any]]


class MessageBase(BaseDataModel):
    _DEFAULT = {
        "id": "",
        "author": "",
        "content": "",
        "target": "",
    }

    def __init__(self) -> None:
        super().__init__()
        self.id: str
        self.author: str
        self.content: str
        self.target: str
