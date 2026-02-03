from unittest import TestCase
import unittest
from textwrap import dedent
from dataclasses import dataclass
from typing import Callable, Any, Dict


@dataclass
class Field:
    """
    Defines a field with a label and preconditions
    """
    label: str
    precondition: Callable[[Any], bool] = None

# Record and supporting classes here
# --- IMPLEMENTATION STARTS HERE ---

class RecordMeta(type):
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        # Get annotations from the class object
        annotations = getattr(cls, '__annotations__', {})
        current_fields = {}
        for f_name, f_type in annotations.items():
            if hasattr(cls, f_name) and isinstance(getattr(cls, f_name), Field):
                field_obj = getattr(cls, f_name)
                # Don't mutate shared Field objects
                field_obj = Field(label=field_obj.label, precondition=field_obj.precondition)
                field_obj.type = f_type
                current_fields[f_name] = field_obj
        # Inherit fields from bases
        full_fields = {}
        for base in reversed(cls.__mro__):
            if hasattr(base, '_fields'):
                full_fields.update(base._fields)
        full_fields.update(current_fields)
        cls._fields = full_fields
        # Create properties for read-only access
        for f_name in full_fields:
            setattr(cls, f_name, property(lambda self, f=f_name: self._data[f]))
        return cls

class Record(metaclass=RecordMeta):
    def __init__(self, **kwargs):
        self._data = {}
        # DEBUG: print argument sets
        #print('kwargs:', kwargs.keys(), 'fields:', self._fields.keys())
        # Check for missing or extra arguments
        if set(kwargs.keys()) != set(self._fields.keys()):
            raise TypeError("Incorrect arguments")
        for name, field in self._fields.items():
            value = kwargs[name]
            # Type Validation
            if not isinstance(value, field.type):
                raise TypeError(f"Field '{name}' must be {field.type.__name__}")
            # Precondition Validation
            if field.precondition and not field.precondition(value):
                raise TypeError(f"Precondition failed for '{name}'")
            self._data[name] = value

    def __setattr__(self, name, value):
        # Prevent modification of fields after __init__
        if hasattr(self, '_fields') and name in self._fields:
            raise AttributeError(f"{name} is read-only")
        super().__setattr__(name, value)

    def __str__(self):
        res = [f"{self.__class__.__name__}("]
        for name, field in self._fields.items():
            res.append(f"  # {field.label}")
            res.append(f"  {name}={repr(self._data[name])}\n")
        return "\n".join(res).strip() + "\n)"

# --- IMPLEMENTATION ENDS HERE ---

# Usage of Record
class Person(Record):
    """
    A simple person record
    """ 
    name: str = Field(label="The name") 
    age: int = Field(label="The person's age", precondition=lambda x: 0 <= x <= 150)
    income: float = Field(label="The person's income", precondition=lambda x: 0 <= x)

class Named(Record):
    """
    A base class for things with names
    """
    name: str = Field(label="The name") 

class Animal(Named):
    """
    An animal
    """
    habitat: str = Field(label="The habitat", precondition=lambda x: x in ["air", "land","water"])
    weight: float = Field(label="The animals weight (kg)", precondition=lambda x: 0 <= x)

class Dog(Animal):
    """
    A type of animal
    """
    bark: str = Field(label="Sound of bark")

# Tests 
class RecordTests(TestCase):
    def test_creation(self):
        Person(name="JAMES", age=110, income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age=160, income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES")
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age=-1, income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age="150", income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age="150", wealth=24000.0)
    
    def test_properties(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        self.assertEqual(james.age, 34)
        with self.assertRaises(AttributeError):
            james.age = 32
    
    def test_str(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        correct = dedent("""
        Person(
          # The name
          name='JAMES'

          # The person's age
          age=34

          # The person's income
          income=24000.0
        )
        """).strip()
        self.assertEqual(str(james), correct)

    def test_dog(self):
        mike = Dog(name="mike", habitat="land", weight=50., bark="ARF")
        self.assertEqual(mike.weight, 50)
        
if __name__ == '__main__':
    unittest.main()