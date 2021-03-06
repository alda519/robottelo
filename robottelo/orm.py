"""Module that define the model layer used to define entities"""
from fauxfactory import FauxFactory
from robottelo.common import helpers
import booby
import booby.fields
import booby.inspection
import booby.validators
import collections
import importlib
import inspect
import random
import urlparse


def _get_value(field, default):
    """Return a value for ``field``.

    Use the following strategies, in order, to find a value for ``field``:

    1. If ``field`` has a default value, return that value.
    2. If ``field`` provides choices, randomly return one of those choices.
    3. If ``default`` is callable, return ``default()``.
    4. Finally, fall back to returning ``default``.

    :param field: A :class:`Field`, or one of its more specialized brethren.
    :param default: A callable which yields a value.
    :return: A value appropriate for that field.

    """
    if 'default' in field.options.keys():
        return field.options['default']
    elif 'choices' in field.options.keys():
        return FauxFactory.generate_choice(field.options['choices'])
    elif callable(default):
        return default()
    else:
        return default


# -----------------------------------------------------------------------------
# Definition of individual entity fields. Wrappers for existing booby fields
# come first, and custom fields come second.
# -----------------------------------------------------------------------------


class BooleanField(booby.fields.Boolean):
    """Field that represents a boolean"""
    def get_value(self):
        """Return a value suitable for a :class:`BooleanField`."""
        return _get_value(self, FauxFactory.generate_boolean)


class EmailField(booby.fields.Email):
    """Field that represents a boolean"""
    def get_value(self):
        """Return a value suitable for a :class:`EmailField`."""
        return _get_value(self, FauxFactory.generate_email)


class FloatField(booby.fields.Float):
    """Field that represents a float"""
    def get_value(self):
        """Return a value suitable for a :class:`FloatField`."""
        return _get_value(self, random.random() * 10000)


class IntegerField(booby.fields.Integer):
    """Field that represents an integer"""
    def __init__(self, min_val=None, max_val=None, *args, **kwargs):
        self.min_val = min_val
        self.max_val = max_val
        super(IntegerField, self).__init__(*args, **kwargs)

    def get_value(self):
        """Return a value suitable for a :class:`IntegerField`."""
        return _get_value(
            self,
            FauxFactory.generate_integer(self.min_val, self.max_val)
        )


class StringField(booby.fields.String):
    """Field that represents a string."""
    def __init__(self, max_len=30, str_type=('utf8',), *args, **kwargs):
        """Constructor for a ``StringField``.

        The default ``max_len`` of string fields is short for two reasons:

        1. Foreman's database backend limits many fields to 255 bytes in
           length. As a result, ``max_len`` should be no longer than 85
           characters long, as 85 unicode characters may be up to 255 bytes
           long.
        2. Humans have to read through the error messages produced by
           Robottelo. Long error messages are hard to read through, and that
           hurts productivity. Thus, a ``max_len`` even shorter than 85 chars
           is desirable.

        :param int max_len: The maximum length of the string generated when
            :meth:`get_value` is called.
        :param sequence str_type: The types of characters to generate when
            :meth:`get-value` is called. Any argument which can be passed to
            ``FauxFactory.generate_string`` can be provided in the sequence.

        """
        self.max_len = max_len
        self.str_type = str_type
        super(StringField, self).__init__(*args, **kwargs)

    def get_value(self):
        """Return a value suitable for a :class:`StringField`."""
        return _get_value(
            self,
            lambda: FauxFactory.generate_string(
                FauxFactory.generate_choice(self.str_type),
                FauxFactory.generate_integer(1, self.max_len)
            )
        )


class Field(booby.fields.Field):
    """Base field class to implement other fields"""


class DateField(Field):
    """Field that represents a date"""


class DateTimeField(Field):
    """Field that represents a datetime"""


class IPAddressField(StringField):
    """Field that represents an IP adrress"""
    def get_value(self):
        """Return a value suitable for a :class:`IPAddressField`."""
        return _get_value(self, FauxFactory.generate_ipaddr)


# FIXME: implement get_value()
class ListField(Field):
    """Field that represents a list of strings"""

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(
            booby.validators.List(booby.validators.String()),
            *args,
            **kwargs
        )


class MACAddressField(StringField):
    """Field that represents a MAC adrress"""
    def get_value(self):
        """Return a value suitable for a :class:`MACAddressField`."""
        return _get_value(self, FauxFactory.generate_mac)


class OneToOneField(booby.fields.Embedded):
    """Field that represents a one to one related entity"""
    def get_value(self):
        """
        Return an instance of the :class:`robottelo.orm.Entity` this field
        points to.
        """
        return _get_class(self.model)()


class OneToManyField(Field):
    """Field that points to zero or more other entities.

    When used in an entity definition, you declare what type of entity this
    field can point to. When that entity is instantiated, the
    ``OneToManyField`` acts as a list that points to other entity instances.
    Roughly speaking, this field acts like a list of foreign keys to a certain
    type of entity.

    There are several ways to assign values to a ``OneToManyField``. You can
    assign a single entity, a list of entities, a dict of entity fields, or a
    list of dicts. For example::

        >>> class PetEntity(Entity):
        ...     name = StringField()
        ...
        >>> class OwnerEntity(Entity):
        ...     pets = OneToManyField(PetEntity)
        ...
        >>> owner = OwnerEntity()
        >>> owner.pets = PetEntity(name='fido')
        >>> len(owner.pets) == 1 and isinstance(owner.pets[0], PetEntity)
        True
        >>> owner.pets = [PetEntity(name='buster')]
        >>> len(owner.pets) == 1 and isinstance(owner.pets[0], PetEntity)
        True
        >>> owner.pets = {'name': 'Liberty'}
        >>> len(owner.pets) == 1 and isinstance(owner.pets[0], PetEntity)
        True
        >>> owner.pets = [{'name': 'Willow'}]
        >>> len(owner.pets) == 1 and isinstance(owner.pets[0], PetEntity)
        True

    The example above shows that the value assigned to a ``OneToManyField`` is
    converted to a list of entity instances.

    """
    def __init__(self, entity, *args, **kwargs):
        """Record the ``entity`` argument and call ``super``."""
        super(OneToManyField, self).__init__(
            booby.validators.List(booby.validators.Model(entity)),
            *args,
            **kwargs
        )
        self.entity = entity

    def __set__(self, instance, value):
        """Manipulate ``value`` before calling ``super``.

        Several types of values are accepted, and the manipulation performed
        varies depending upon the type of ``value``:

        * If ``value`` is a single entity instance it is placed into a list.
        * If ``value`` is a dict, it is converted to an instance of type
          ``self.entity`` and placed into a list.
        * If the value is a list and it contains any dicts, those dicts are
          converted to instances of type ``self.entity``.

        """
        if isinstance(value, self.entity):
            # entity -> [entity]
            value = [value]
        elif isinstance(value, collections.MutableMapping):
            # {dict} -> [entity]
            value = [self.entity(**value)]
        elif isinstance(value, collections.MutableSequence):
            # [entity, {dict}] -> [entity, entity]
            for index, val in enumerate(value):
                if isinstance(val, collections.MutableMapping):
                    value[index] = self.entity(**val)
        super(OneToManyField, self).__set__(instance, value)

    def get_value(self):
        """
        Return a list of :class:`robottelo.orm.Entity` instances of type
        ``self.entity``.
        """
        return [_get_class(self.entity)()]


class URLField(StringField):
    """Field that represents an URL"""
    def get_value(self):
        """Return a value suitable for a :class:`URLField`."""
        return _get_value(self, FauxFactory.generate_url)


def _get_class(class_or_name, module='robottelo.entities'):
    """Return a class object.

    If ``class_or_name`` is a class, it is returned untouched. Otherwise,
    ``class_or_name`` is assumed to be a string. In this case,
    :mod:`robottelo.entities` is searched for a class by that name and
    returned.

    :param class_or_name: Either a class or the name of a class.
    :param str module: A dotted module name.
    :return: Either the class passed in or a class from ``module``.

    """
    if inspect.isclass(class_or_name):
        return class_or_name
    return getattr(importlib.import_module(module), class_or_name)


# -----------------------------------------------------------------------------
# Definition of parent Entity class and its dependencies.
# -----------------------------------------------------------------------------


class NoSuchPathError(Exception):
    """Indicates that the requested path cannot be constructed."""


class Entity(booby.Model):
    """A logical representation of a Foreman entity.

    This class is rather useless as is, and it is intended to be subclassed.
    Subclasses can specify two useful types of information:

    * fields
    * metadata

    Fields are represented by setting class attributes, and metadata is
    represented by settings attributes on the inner class named ``Meta``.

    """
    # The id() builtin is still available within instance methods, class
    # methods, static methods, inner classes, and so on. However, id() is *not*
    # available at the current level of lexical scoping after this point.
    id = IntegerField()  # pylint:disable=C0103

    class Meta(object):
        """Non-field information about this entity.

        This class is a convenient place to store any non-field information
        about an entity. For example, you can add the ``api_path`` and
        ``api_names`` variables. See :meth:`robottelo.orm.Entity.path` and
        :meth:`robottelo.factory.EntityFactoryMixin._factory_data` for
        details on the two variables, respectively.
        """

    def path(self, which=None):
        """Return the path to the current entity.

        Return the path to all entities of this entity's type if:

        * ``which`` is ``'all'``, or
        * ``which`` is ``None`` and instance attribute ``id`` is unset.

        Return the path to this exact entity if instance attribute ``id`` is
        set and:

        * ``which`` is ``'this'``, or
        * ``which`` is ``None``.

        Raise :class:`NoSuchPathError` otherwise.

        Child classes may choose to extend this method, especially if a child
        entity offers more than the two URLs supported by default. If extended,
        then the extending class should check for custom parameters before
        calling ``super``::

            def path(self, which):
                if which == 'custom':
                    return urlparse.urljoin(...)
                super(ChildEntity, self).__init__(which)

        This will allow the extending method to accept a custom parameter
        without accidentally raising a :class:`NoSuchPathError`.

        :param str which: Optional. Valid arguments are 'this' and 'all'.
        :return: A fully qualified URL.
        :rtype: str
        :raises robottelo.orm.NoSuchPathError: If no path can be built.

        """
        # (no-member) pylint:disable=E1101
        # It is OK that member ``self.Meta.api_path`` is not found. Subclasses
        # are required to set that attribute if they wish to use this method.
        #
        # Beware of leading and trailing slashes:
        #
        # urljoin('example.com', 'foo') => 'foo'
        # urljoin('example.com/', 'foo') => 'example.com/foo'
        # urljoin('example.com', '/foo') => '/foo'
        # urljoin('example.com/', '/foo') => '/foo'
        base = urlparse.urljoin(
            helpers.get_server_url() + '/',
            self.Meta.api_path
        )
        if which == 'all' or which is None and self.id is None:
            return base
        elif self.id is not None and (which is None or which == 'this'):
            return urlparse.urljoin(base + '/', str(self.id))
        raise NoSuchPathError

    @classmethod
    def get_fields(cls):
        """Return all defined fields as a dictionary.

        :return: A dictionary mapping ``str`` field names to ``robottelo.orm``
            field types.
        :rtype: dict

        """
        return booby.inspection.get_fields(cls)

    # FIXME: See GitHub issue #1082.
    def get_values(self):
        """Return all field values as a dictionary.

        All fields with a value of ``None`` are omitted from the returned dict.
        For example, if this entity is created::

            SomeEntity(name='foo', description=None)

        This dict is returned::

            {'name': 'foo'}

        This is a bug. See GitHub issue #1082.

        :return: A dictionary mapping field names to field values.
        :rtype: dict

        """
        fields = dict(self)
        for key, value in fields.items():
            if value is None:
                fields.pop(key)
        return fields
