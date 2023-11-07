#
# Copyright © European Union 2022
#
# Licensed under the EUPL, Version 1.2 or – as soon they will be approved by
# the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the Licence for the specific language governing permissions and limitations under the Licence.
#

from typing import Dict

from functools import wraps

from bitstring import BitArray
from ..structures.fields_information import Field, field_info
from ..utils.exceptions import FieldValueNotRecognized


def to_bitarray(func):
    @wraps(func)
    def wrapper_to_bitarray(self, *args, **kwargs):
        input_value = args[-1]

        if isinstance(input_value, Field):
            if isinstance(input_value.value, int):
                input_value = BitArray(uint=input_value.value, length=input_value.size)
            else:
                try:
                    input_value.value = BitArray(input_value.value)
                except TypeError:
                    raise FieldValueNotRecognized(f"Field value types are int, str or BitArray equivalents."
                                                  f" Not {type(input_value.value)}.")
        elif isinstance(input_value, int):
            field_name = args[-2]
            input_value = BitArray(uint=input_value, length=self.get_size(field_name))
        else:
            try:
                input_value = BitArray(input_value)
            except TypeError:
                raise FieldValueNotRecognized(f"Value types are int, str or BitArray equivalents."
                                              f" Not {type(input_value)}.")
        return func(self, *args[:-1], input_value, **kwargs)
    return wrapper_to_bitarray


class DSM:

    def __init__(self):

        self.size_blocks = None
        self.size_bits = None
        self.verified = False
        self.fields: Dict[str, Field] = {}

        for name, field in field_info.items(): # TODO: Search for alternative only load necessary fields
            self.fields[name] = Field(field['name'], None, field['size'])

    @to_bitarray
    def set_value(self, name, value):
        self.fields[name].value = value
        self._extra_actions(name)

    def get_value(self, name) -> BitArray:
        return self.fields[name].value

    def set_size(self, name, size):
        self.fields[name].size = size

    def get_size(self, name):
        return self.fields[name].size

    @to_bitarray
    def set_field(self, field):
        self.fields[field.name] = field
        self._extra_actions(field.name)

    def get_field(self, name):
        return self.fields[name]

    def is_verified(self):
        return self.verified

    def _extra_actions(self, name):
        pass

    @to_bitarray
    def process_structure_data(self, structure, data_stream):
        bit_counter = 0
        for field in structure:
            self.set_value(field, data_stream[bit_counter:bit_counter + self.get_size(field)])
            bit_counter += self.get_size(field)
