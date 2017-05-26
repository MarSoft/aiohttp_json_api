import collections

import attr

from .utils import Symbol

ARG_DEFAULT = Symbol('ARG_DEFAULT')
ResourceID = collections.namedtuple('ResourceID', ['type', 'id'])


@attr.s
class Registry:
    schema_by_type = attr.ib(default=attr.Factory(dict))
    schema_by_resource = attr.ib(default=attr.Factory(dict))

    def get_schema(self, obj, default=ARG_DEFAULT):
        """
        Returns the :class:`~jsonapi.schema.schema.Schema` associated with *o*.
        *o* must be either a typename, a resource class or resource object.

        :param obj:
            A typename, resource object or a resource class
        :param default:
            Returned if no schema for *obj* is found.
        :raises KeyError:
            If no schema for *o* is found and no *default* value is given.
        """
        schema = (
            self.schema_by_resource.get(type(obj)) or
            self.schema_by_resource.get(obj) or
            self.schema_by_type.get(obj)
        )

        if schema is not None:
            return schema
        if default != ARG_DEFAULT:
            return default
        raise KeyError()

    def ensure_identifier(self, obj, asdict=False) -> ResourceID:
        """
        Does the same as :meth:`ensure_identifier_object`, but returns the two
        tuple identifier object instead of the document:

        .. code-block:: python3

            # (typename, id)
            ("people", "42")

        :arg obj:
            A two tuple ``(typename, id)``, a resource object or a resource
            document, which contains the *id* and *type* key
            ``{"type": ..., "id": ...}``.
        """
        result = None

        if isinstance(obj, collections.Sequence):
            assert len(obj) == 2
            result = ResourceID(str(obj[0]), str(obj[1]))
        elif isinstance(obj, collections.Mapping):
            result = ResourceID(str(obj['type']), str(obj['id']))
        else:
            schema = self.get_schema(obj)
            result = ResourceID(schema.type, schema._get_id(obj))

        return result._asdict() if asdict and result else result
