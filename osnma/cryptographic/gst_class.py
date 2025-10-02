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

from typing import Union

from bitstring import BitArray

LEN_GST = 32
LEN_WN = 12
LEN_TOW = 20

WN_MODULO = 4096
MAX_TOW = 604799
MIN_TOW = 0


class GST:

    def __init__(self, *args, **kwargs):
        self.initialized = True
        if len(args) == 0 and len(kwargs) == 0:
            self.initialized = False
            self.wn = None
            self.tow = None
        elif len(args) > 0:
            gst = args[0]
            self.wn = gst[:LEN_WN].uint
            self.tow = gst[LEN_WN:].uint
        else:
            self.wn = kwargs.get('wn', 0)
            self.tow = kwargs.get('tow', 0)

            if self.tow < 0:
                q, r = divmod(self.tow, MAX_TOW+1)
                self.wn += q
                self.tow = r

    def __str__(self):
        return f"{self.wn} {self.tow}"

    ### Logical operators ###

    def __bool__(self):
        return self.initialized

    def __eq__(self, other: Union['GST', BitArray, int]):

        if not self.initialized and not other.initialized:
            return True
        elif self.initialized ^ other.initialized:
            return False

        if isinstance(other, int):
            other = GST(tow=other)
        return self.int == other.int

    def __lt__(self, other: Union['GST', BitArray, int]):
        if isinstance(other, int):
            other = GST(tow=other)
        return self.int < other.int

    def __le__(self, other: Union['GST', BitArray, int]):
        if isinstance(other, int):
            other = GST(tow=other)
        return self.int <= other.int

    def __gt__(self, other: Union['GST', BitArray, int]):
        if isinstance(other, int):
            other = GST(tow=other)
        return self.int > other.int

    def __ge__(self, other: Union['GST', BitArray, int]):
        if isinstance(other, int):
            other = GST(tow=other)
        return self.int >= other.int

    ### Addition ###

    def __add__(self, other: Union[int, 'GST']) -> 'GST':
        if isinstance(other, int):
            tow = self.tow + other
            wn = self.wn
        elif isinstance(other, GST):
            tow = self.tow + other.tow
            wn = self.wn + other.wn
        else:
            raise TypeError(f"Type {type(other)} not supported for addition.")

        if tow > MAX_TOW:
            q, r = divmod(tow, MAX_TOW+1)
            wn += q
            tow = r

        return GST(tow=tow, wn=wn)

    ### Subtraction ###

    def __sub__(self, other: Union[int, 'GST']) -> 'GST':
        if isinstance(other, int):
            tow = self.tow - other
            wn = self.wn
        elif isinstance(other, GST):
            tow = self.tow - other.tow
            wn = self.wn - other.wn
        else:
            raise TypeError(f"Type {type(other)} not supported for subtraction.")

        if tow < MIN_TOW:
            q, r = divmod(tow, MAX_TOW+1)
            wn += q
            tow = r

        return GST(tow=tow, wn=wn)

    def __floordiv__(self, other: int) -> int:
        return self.total_seconds // other

    def __mod__(self, other: int) -> int:
        return self.tow % other

    ### Accessors ###

    @property
    def bitarray(self):
        return BitArray(uint=self.wn << LEN_TOW | self.tow, length=LEN_GST)

    @property
    def tow_bitarray(self):
        return BitArray(uint=self.tow, length=LEN_TOW)

    @property
    def wn_bitarray(self):
        return BitArray(uint=self.wn, length=LEN_WN)

    @property
    def int(self):
        return self.wn << LEN_TOW | self.tow

    @property
    def total_seconds(self):
        return (self.wn * (MAX_TOW+1)) + self.tow

    @property
    def subframe(self):
        return GST(wn=self.wn, tow=self.tow - self.tow % 30)


if __name__ == '__main__':

    a = GST()
    if a:
        print(a)

    print("GST0")
    bitarray_0 = BitArray(uint=0, length=12) + BitArray(uint=1000, length=20)
    gst0 = GST(bitarray_0)
    print(f"Constructor value:\t{bitarray_0}")
    print(f"Print value:\t\t{gst0}")

    print("\nGST1")
    gst1 = GST(wn=2100, tow=22223)
    print(f"Constructor value:\t2100 22223")
    print(f"Print value:\t\t{gst1}")


