"""
Application registry
====================
"""
import collections
import inspect

from .common import ResourceID
from .typings import ResourceIdentifier


class Registry(collections.UserDict):
    __slots__ = ('data',)

    def __getitem__(self, key):
        return super(Registry, self).__getitem__(
            key if isinstance(key, str) or inspect.isclass(key) else type(key)
        )

    def ensure_identifier(self, obj, asdict=False) -> ResourceIdentifier:
        """
        Returns the identifier object (:class:`ResourceID`) for the *resource*:

        .. code-block:: python3

            >>> registry.ensure_identifier({'type': 'something', 'id': 123})
            ResourceID(type='something', id='123')

        :arg obj:
            A two tuple ``(typename, id)``, a resource object or a resource
            document, which contains the *id* and *type* key
            ``{"type": ..., "id": ...}``.
        :arg bool asdict:
            Return ResourceID as dictionary if true
        """
        if isinstance(obj, collections.Sequence) and len(obj) == 2:
            result = ResourceID(str(obj[0]), str(obj[1]))
        elif isinstance(obj, collections.Mapping):
            result = ResourceID(str(obj['type']), str(obj['id']))
        else:
            schema = self.data[type(obj)]
            result = ResourceID(schema.type, schema.get_object_id(obj))

        return result._asdict() if asdict and result else result
