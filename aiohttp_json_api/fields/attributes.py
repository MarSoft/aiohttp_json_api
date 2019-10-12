"""
Fields
======

.. note::

    Always remember that you can model the JSON API completly with the fields
    in :mod:`~aiohttp_json_api.schema.base_fields`.

.. sidebar:: Index

    *   :class:`String`
    *   :class:`Integer`
    *   :class:`Float`
    *   :class:`Complex`
    *   :class:`Decimal`
    *   :class:`Fraction`
    *   :class:`DateTime`
    *   :class:`TimeDelta`
    *   :class:`UUID`
    *   :class:`Boolean`
    *   :class:`URI`
    *   :class:`Email`
    *   :class:`Dict`
    *   :class:`List`
    *   :class:`Number`
    *   :class:`Str`
    *   :class:`Bool`

This module contains fields for several standard Python types and classes
from the standard library.
"""
import collections
import datetime
import decimal
import fractions
import uuid
from enum import Enum
from typing import Optional, Collection, Any, Union, Type, MutableMapping, Tuple as TypingTuple

import trafaret as t
from trafaret.contrib import rfc_3339
from yarl import URL

from aiohttp_json_api.errors import InvalidType, InvalidValue
from aiohttp_json_api.fields.base import Attribute
from aiohttp_json_api.fields.trafarets import DecimalTrafaret
from aiohttp_json_api.helpers import is_collection
from aiohttp_json_api.jsonpointer import JSONPointer
from aiohttp_json_api.schema import BaseSchema

__all__ = (
    'String',
    'Integer',
    'Float',
    'Complex',
    'Decimal',
    'Fraction',
    'DateTime',
    'TimeDelta',
    'UUID',
    'Boolean',
    'URI',
    'Email',
    'Dict',
    'List',
    'Number',
    'Str',
    'Bool',
)

ComparableNumber = Union[int, float]


class String(Attribute):
    def __init__(
        self,
        *,
        allow_blank: bool = False,
        regex: Optional[str] = None,
        choices: Optional[Union[Collection[str], Type[Enum]]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if regex is not None:
            self._trafaret = t.Regexp(regex)
        else:
            self._trafaret = t.String(allow_blank=allow_blank, min_length=min_length, max_length=max_length)

        self.choices: Optional[Union[Collection[str], Type[Enum]]] = None
        if choices is not None and is_collection(choices):
            if isinstance(choices, type(Enum)):
                self.choices = choices
                self._trafaret &= t.Enum(*choices.__members__.keys())
            else:
                self._trafaret &= t.Enum(*choices)

        if self.allow_none:
            self._trafaret |= t.Null()

    def pre_validate(self, data: str, sp: JSONPointer) -> None:
        try:
            self._trafaret.check(data)
        except t.DataError as error:
            detail = error.as_dict()
            if self.choices is not None:
                possible_values = (
                    self.choices
                    if not isinstance(self.choices, type(Enum))
                    else self.choices.__members__.keys()
                )
                detail += ' ({})'.format(', '.join(possible_values))
            raise InvalidValue(detail=detail, source_pointer=sp)

    def deserialize(self, data: str, sp: JSONPointer, **kwargs) -> Optional[Union[str, Enum]]:
        return (
            self.choices[data]
            if isinstance(self.choices, type(Enum)) and data in self.choices.__members__
            else data
        )

    def serialize(self, data: Union[str, Type[Enum]], **kwargs) -> Optional[str]:
        if isinstance(data, type(Enum)):
            result = self._trafaret.check(data.name)
        else:
            result = self._trafaret.check(data)
        return result


class Integer(Attribute):
    def __init__(
        self,
        *,
        gte: Optional[int] = None,
        lte: Optional[int] = None,
        gt: Optional[int] = None,
        lt: Optional[int] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._trafaret = t.Int(gte=gte, lte=lte, gt=gt, lt=lt)
        if self.allow_none:
            self._trafaret |= t.Null()

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        try:
            self._trafaret.check(data)
        except t.DataError as error:
            raise InvalidValue(detail=error.as_dict(), source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> Optional[int]:
        return self._trafaret.check(data)

    def serialize(self, data: Any, **kwargs: Any) -> Optional[int]:
        return self._trafaret.check(data)


class Float(Attribute):
    def __init__(
        self,
        *,
        gte: Optional[ComparableNumber] = None,
        lte: Optional[ComparableNumber] = None,
        gt: Optional[ComparableNumber] = None,
        lt: Optional[ComparableNumber] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._trafaret = t.Float(gte=gte, lte=lte, gt=gt, lt=lt)
        if self.allow_none:
            self._trafaret |= t.Null()

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        try:
            self._trafaret.check(data)
        except t.DataError as error:
            raise InvalidValue(detail=error.as_dict(), source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> Optional[float]:
        return self._trafaret.check(data)

    def serialize(self, data: Any, **kwargs: Any) -> Optional[float]:
        return self._trafaret.check(data)


class Complex(Attribute):
    """
    Encodes a :class:`complex` number as JSON object with a *real* and *imag*
    member::

        {"real": 1.2, "imag": 42}
    """
    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        detail = "Must be an object with a 'real' and 'imag' member.'"

        if not isinstance(data, collections.Mapping):
            raise InvalidType(detail=detail, source_pointer=sp)
        if 'real' not in data:
            detail = "Does not have a 'real' member."
            raise InvalidValue(detail=detail, source_pointer=sp)
        if 'imag' not in data:
            detail = "Does not have an 'imag' member."
            raise InvalidValue(detail=detail, source_pointer=sp)

        if not isinstance(data['real'], (int, float)):
            detail = 'The real part must be a number.'
            raise InvalidValue(detail=detail, source_pointer=sp / 'real')
        if not isinstance(data['imag'], (int, float)):
            detail = 'The imaginar part must be a number.'
            raise InvalidValue(detail=detail, source_pointer=sp / 'imag')

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> complex:
        return complex(data['real'], data['imag'])

    def serialize(self, data: Any, **kwargs: Any) -> MutableMapping[str, float]:
        data = complex(data)
        return {'real': data.real, 'imag': data.imag}


class Decimal(Attribute):
    """Encodes and decodes a :class:`decimal.Decimal` as a string."""
    def __init__(
        self,
        *,
        gte: Optional[ComparableNumber] = None,
        lte: Optional[ComparableNumber] = None,
        gt: Optional[ComparableNumber] = None,
        lt: Optional[ComparableNumber] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._trafaret = DecimalTrafaret(gte=gte, lte=lte, gt=gt, lt=lt)
        if self.allow_none:
            self._trafaret |= t.Null()

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        try:
            self._trafaret.check(data)
        except t.DataError as error:
            raise InvalidValue(detail=error.as_dict(), source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> Optional[decimal.Decimal]:
        if self.allow_none and data is None:
            return None

        return self._trafaret.check(data)

    def serialize(self, data: Any, **kwargs: Any) -> Optional[str]:
        if self.allow_none and data is None:
            return None

        return str(self._trafaret.check(data))


class Fraction(Attribute):
    """Stores a :class:`fractions.Fraction` in an object with a *numerator*
    and *denominator* member::

        # 1.5
        {"numerator": 2, "denominator": 3}

    :arg float min:
        The fraction must be greater or equal than this value.
    :arg float max:
        The fraction must be less or equal than this value.
    """

    def __init__(
        self,
        *,
        min: Optional[ComparableNumber] = None,
        max: Optional[ComparableNumber] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        # min must be <= max
        assert min is None or max is None or min <= max

        self.min = min
        self.max = max

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        if not isinstance(data, dict):
            detail = "Must be an object with a 'numerator' and 'denominator' member."
            raise InvalidType(detail=detail, source_pointer=sp)
        if 'numerator' not in data:
            detail = "Does not have a 'numerator' member."
            raise InvalidValue(detail=detail, source_pointer=sp)
        if 'denominator' not in data:
            detail = "Does not have a 'denominator' member."
            raise InvalidValue(detail=detail, source_pointer=sp)

        if not isinstance(data['numerator'], int):
            detail = 'The numerator must be an integer.'
            raise InvalidValue(detail=detail, source_pointer=sp / 'numerator')
        if not isinstance(data['denominator'], int):
            detail = 'The denominator must be an integer.'
            raise InvalidValue(detail=detail, source_pointer=sp / 'denominator')
        if data['denominator'] == 0:
            detail = 'The denominator must be not equal to zero.'
            raise InvalidValue(detail=detail, source_pointer=sp / 'denominator')

        val = data['numerator'] / data['denominator']
        if self.min is not None and self.min > val:
            detail = f'Must be >= {self.min}.'
            raise InvalidValue(detail=detail, source_pointer=sp)
        if self.max is not None and self.max < val:
            detail = f'Must be <= {self.max}.'
            raise InvalidValue(detail=detail, source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> fractions.Fraction:
        return fractions.Fraction(int(data[0]), int(data[1]))

    def serialize(self, data: Any, **kwargs: Any) -> MutableMapping[str, int]:
        return {'numerator': data.numerator, 'denominator': data.denominator}


class DateTime(Attribute):
    """
    Stores a :class:`datetime.datetime` in ISO-8601 as recommended in
    http://jsonapi.org/recommendations/#date-and-time-fields.
    """

    def __init__(self, *, allow_blank: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._trafaret = rfc_3339.DateTime(allow_blank=allow_blank)
        if self.allow_none:
            self._trafaret |= t.Null()

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        try:
            self._trafaret.check(data)
        except t.DataError as error:
            raise InvalidValue(detail=error.as_dict(), source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> Optional[datetime.datetime]:
        return self._trafaret.check(data)

    def serialize(self, data: Any, **kwargs: Any) -> Optional[str]:
        if isinstance(data, datetime.datetime):
            return data.isoformat()

        return self._trafaret.check(data)


class Date(Attribute):
    """
    Stores a :class:`datetime.datetime` in ISO-8601 as recommended in
    http://jsonapi.org/recommendations/#date-and-time-fields.
    """
    def __init__(self, *, allow_blank: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._trafaret = rfc_3339.Date(allow_blank=allow_blank)
        if self.allow_none:
            self._trafaret |= t.Null()

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        try:
            self._trafaret.check(data)
        except t.DataError as error:
            raise InvalidValue(detail=error.as_dict(), source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> Optional[datetime.date]:
        return self._trafaret.check(data)

    def serialize(self, data: Any, **kwargs: Any) -> Optional[str]:
        if isinstance(data, datetime.date):
            return data.isoformat()

        return self._trafaret.check(data)


class TimeDelta(Attribute):
    """
    Stores a :class:`datetime.timedelta` as total number of seconds.

    :arg datetime.timedelta min:
        The timedelta must be greater or equal than this value.
    :arg datetime.timedelta max:
        The timedelta must be less or equal than this value.
    """

    def __init__(
        self,
        *,
        min: Optional[datetime.timedelta] = None,
        max: Optional[datetime.timedelta] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        # min must be <= max
        assert min is None or max is None or min <= max

        self.min = min
        self.max = max

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        try:
            data = float(data)
        except TypeError:
            detail = "Must be a number."
            raise InvalidType(detail=detail, source_pointer=sp)

        data = datetime.timedelta(seconds=data)

        if self.min is not None and self.min > data:
            detail = f'The timedelta must be >= {self.min}.'
            raise InvalidValue(detail=detail, source_pointer=sp)
        if self.max is not None and self.max < data:
            detail = f'The timedelta must be <= {self.max}.'
            raise InvalidValue(detail=detail, source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> datetime.timedelta:
        return datetime.timedelta(seconds=float(data))

    def serialize(self, data: Any, **kwargs: Any) -> int:
        return data.total_seconds()


class UUID(Attribute):
    """
    Encodes and decodes a :class:`uuid.UUID`.

    :arg int version: The required version of the UUID.
    """
    def __init__(self, *, version: int = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.version = version

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        if self.allow_none and data is None:
            return

        if not isinstance(data, str):
            detail = 'The UUID must be a hexadecimal string.'
            raise InvalidType(detail=detail, source_pointer=sp)

        try:
            data = uuid.UUID(hex=data)
        except ValueError:
            detail = 'The UUID is badly formed (the representation as hexadecimal string is needed).'
            raise InvalidValue(detail=detail, source_pointer=sp)

        if self.version is not None and self.version != data.version:
            detail = f'Not a UUID{self.version}.'
            raise InvalidValue(detail=detail, source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> Optional[uuid.UUID]:
        if self.allow_none and data is None:
            return None
        return uuid.UUID(hex=data)

    def serialize(self, data: Any, **kwargs: Any) -> Optional[str]:
        if self.allow_none and data is None:
            return None
        return data.hex


class Boolean(Attribute):
    """
    Ensures that the input is a :class:`bool`.
    """
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._trafaret = t.Bool()
        if self.allow_none:
            self._trafaret |= t.Null()

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        try:
            self._trafaret.check(data)
        except t.DataError as error:
            raise InvalidType(detail=error.as_dict(), source_pointer=sp)

    def serialize(self, data: Any, **kwargs: Any) -> Optional[bool]:
        return self._trafaret.check(data)


class URI(Attribute):
    """Parses the URI with :func:`rfc3986.urlparse` and returns the result."""
    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        if not isinstance(data, str):
            detail = 'Must be a string.'
            raise InvalidType(detail=detail, source_pointer=sp)
        try:
            URL(data)
        except ValueError:
            detail = 'Not a valid URI.'
            raise InvalidValue(detail=detail, source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> URL:
        return URL(data)

    def serialize(self, data: Any, **kwargs: Any) -> str:
        return str(data)


class Email(Attribute):
    """Checks if a string is syntactically correct Email address."""
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._trafaret = t.Email
        if self.allow_none:
            self._trafaret |= t.Null

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        try:
            self._trafaret.check(data)
        except t.DataError:
            if not isinstance(data, str):
                detail = 'Must be a string.'
                raise InvalidType(detail=detail, source_pointer=sp)
            else:
                detail = 'Not a valid Email address.'
                raise InvalidValue(detail=detail, source_pointer=sp)

    def serialize(self, data: Any, **kwargs: Any) -> Optional[str]:
        return self._trafaret.check(data)


class Dict(Attribute):
    """
    Realises a dictionary which has only values of a special field::

        todo = Dict(String(regex=".*[A-z0-9].*"))

    .. note::

        If you deal with dictionaries with values of different types, you can still use the more general
        :class:`~aiohttp_json_api.schema.base_fields.Attribute` field to model this data.

        *You are not forced to use a* :class:`Dict` *field*! It is only a helper.

    :arg Attribute field:
        All values of the dictionary are encoded and decoded using this field.
    """

    def __init__(self, field: Attribute, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.field = field

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> MutableMapping[str, Any]:
        return {
            key: self.field.deserialize(schema, value, sp / key)
            for key, value in data.items()
        }

    def serialize(self, data: Any, **kwargs: Any) -> MutableMapping[str, Any]:
        return {
            key: self.field.serialize(schema, value)
            for key, value in data.items()
        }


class List(Attribute):
    """
    .. note::

        If your list has items of different types, you can still use the more
        general :class:`~aiohttp_json_api.schema.base_fields.Attribute`
        field to model this data.

        *You are not forced to use a* :class:`List` *field*! It is only a
        helper.

    :arg Attribute field:
        All values of the list are encoded and decoded using this field.
    """
    def __init__(self, field: Attribute, min_length: int = 0, max_length: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.field = field
        self._trafaret = t.List(field._trafaret, min_length=min_length, max_length=max_length)
        if self.allow_none:
            self._trafaret |= t.Null

    def pre_validate(self, data: Any, sp: JSONPointer) -> None:
        try:
            self._trafaret.check(data)
        except t.DataError as error:
            raise InvalidValue(detail=error.as_dict(), source_pointer=sp)

    def deserialize(self, data: Any, sp: JSONPointer, **kwargs: Any) -> Optional[Collection[Any]]:
        if self.allow_none and data is None:
            return None

        return [
            self.field.deserialize(schema, item, sp / str(index))
            for index, item in enumerate(data)
        ]

    def serialize(self, data: Any, **kwargs: Any) -> Optional[Collection[Any]]:
        if self.allow_none and data is None:
            return None

        return [self.field.serialize(schema, item) for item in data]


class Tuple(List):
    def deserialize(
        self,
        schema: BaseSchema,
        data: Any,
        sp: JSONPointer,
        **kwargs: Any,
    ) -> Optional[TypingTuple[Any, ...]]:
        result = super().deserialize(schema, data, sp, **kwargs)
        return tuple(result) if result is not None else result

    def serialize(self, data: Any, **kwargs: Any) -> Optional[TypingTuple[Any, ...]]:
        result = super().serialize(schema, data, **kwargs)
        return tuple(result) if result is not None else result


# Some aliases.
Number = Float
Str = String
Bool = Boolean
