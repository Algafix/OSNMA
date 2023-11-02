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

mac_lookup_table = [
    {
        'ID': 0,
        'sections': 1,
        'NMACK': 1,
        'MACs': 14,
        'sequence': ['00S','00E','00E','00E','00E','00E','00E','00S','00E','00E','00E','00E','00E','00E']
    },
    {
        'ID': 1,
        'sections': 1,
        'NMACK': 1,
        'MACs': 14,
        'sequence': ['00S','00G','00G','00G','00G','00E','00E','00E','00E','00E','00E','00S','00G','00G']
    },
    {
        'ID': 2,
        'sections': 1,
        'NMACK': 1,
        'MACs': 14,
        'sequence': ['00S','FLX','FLX','FLX','FLX','FLX','FLX','FLX','FLX','FLX','FLX','FLX','FLX','FLX']
    },
    {
        'ID': 3,
        'sections': 1,
        'NMACK': 1,
        'MACs': 14,
        'sequence': ['00S','04S','03S','00E','00E','00E','00E','FLX','FLX','FLX','11S','12S','FLX','FLX']
    },
    {
        'ID': 4,
        'sections': 1,
        'NMACK': 1,
        'MACs': 14,
        'sequence': ['00S','04S','03S','00G','00G','00E','00E','FLX','FLX','FLX','11S','12S','FLX','FLX']
    },
    {
        'ID': 5,
        'sections': 1,
        'NMACK': 1,
        'MACs': 14,
        'sequence': ['00S','03S','05S','00E','FLX','04S','05G','00E','FLX','05E','12S','11S','FLX','FLX']
    },
    {
        'ID': 6,
        'sections': 1,
        'NMACK': 1,
        'MACs': 14,
        'sequence': ['00S','03S','05S','00E','04S','05E','FLX','12S','FLX','FLX','FLX','FLX','FLX','FLX']
    },
    {
        'ID': 7,
        'sections': 1,
        'NMACK': 1,
        'MACs': 14,
        'sequence': ['00S','FLX','FLX','FLX','00E','00E','00E','FLX','FLX','FLX','11S','12S','FLX','FLX']
    },
    {
        'ID': 8,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','00E','00E','00E','00E'],['00S','00E','00E','00E','00E']]
    },
    {
        'ID': 9,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','00G','00G','00G','00G'],['00S','00E','00E','00E','00E']]
    },
    {
        'ID': 10,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','FLX','FLX','FLX','FLX'],['00S','00E','00E','00E','00E']]
    },
    {
        'ID': 11,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','FLX','FLX','00E','11S'],['00S','00E','00E','00E','12S']]
    },
    {
        'ID': 12,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','FLX','FLX','00G','11S'],['00S','00G','00E','00E','12S']]
    },
    {
        'ID': 13,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','03S','05S','FLX','00E'],['05E','00E','04S','00E','12S']]
    },
    {
        'ID': 14,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','03S','05S','FLX','00E'],['05E','05G','04S','00G','12S']]
    },
    {
        'ID': 15,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','04S','FLX','FLX','11S'],['00S','00E','00E','00E','12S']]
    },
    {
        'ID': 16,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','12S','00E','00E','FLX'],['00S','11S','00E','00E','00E']]
    },
    {
        'ID': 17,
        'sections': 1,
        'NMACK': 2,
        'MACs': 5,
        'sequence': [['00S','FLX','FLX','00G','FLX'],['00S','00E','00E','12S','11S']]
    },
    {
        'ID': 18,
        'sections': 2,
        'NMACK': 3,
        'MACs': 2,
        'sequence': [[['00S','00E'], ['00E','00E'], ['00E','00E']],[['00S','00E'], ['00E','00E'], ['00E','00E']]]
    },
    {
        'ID': 19,
        'sections': 2,
        'NMACK': 3,
        'MACs': 2,
        'sequence': [[['00S','00G'], ['00G','00G'], ['00G','00G']],[['00S','00E'], ['00E','00E'], ['00E','00E']]]
    },
    {
        'ID': 20,
        'sections': 2,
        'NMACK': 3,
        'MACs': 2,
        'sequence': [[['00S','FLX'], ['00E','00E'], ['00E','00E']],[['00S','FLX'], ['00E','00E'], ['00E','00E']]]
    },
    {
        'ID': 21,
        'sections': 2,
        'NMACK': 3,
        'MACs': 2,
        'sequence': [[['00S','FLX'], ['00E','00E'], ['00E','11S']],[['00S','FLX'], ['00E','00E'], ['00E','12S']]]
    },
    {
        'ID': 22,
        'sections': 2,
        'NMACK': 3,
        'MACs': 2,
        'sequence': [[['00S','FLX'], ['00G','00G'], ['00G','11S']],[['00S','FLX'], ['00E','00E'], ['00E','12S']]]
    },
    {
        'ID': 23,
        'sections': 2,
        'NMACK': 3,
        'MACs': 2,
        'sequence': [[['00S','FLX'], ['05S','03S'], ['00E','11S']],[['00S','FLX'], ['04S','00E'], ['05E','12S']]]
    },
    {
        'ID': 24,
        'sections': 2,
        'NMACK': 3,
        'MACs': 2,
        'sequence': [[['00S','FLX'], ['05S','03S'], ['00G','11S']],[['00S','FLX'], ['04S','00G'], ['05E','12S']]]
    },
    None,
    None,
    {
        'ID': 27,
        'sections': 2,
        'NMACK': 1,
        'MACs': 6,
        'sequence': [['00S', '00E', '00E', '00E', '12S', '00E'], ['00S', '00E', '00E', '04S', '12S', '00E']]
    },
    {
        'ID': 28,
        'sections': 2,
        'NMACK': 1,
        'MACs': 10,
        'sequence': [['00S', '00E', '00E', '00E', '00S', '00E', '00E', '12S', '00E', '00E'],
                     ['00S', '00E', '00E', '00S', '00E', '00E', '04S', '12S', '00E', '00E']]
    },
    {
        'ID': 29,
        'sections': 2,
        'NMACK': 1,
        'MACs': 6,
        'sequence': [['00S', '00E', '12E', '00G', '12S', '00E'], ['00S', '00G', '00E', '04S', '12S', '00E']]
    },
    {
        'ID': 30,
        'sections': 2,
        'NMACK': 2,
        'MACs': 4,
        'sequence': [[['00S', '00E', '12S', '00E'], ['00S', '00E', '12E', '00E']],
                     [['00S', '00E', '12S', '00E'], ['00S', '04S', '12E', '00E']]]
    },
    {
        'ID': 31,
        'sections': 2,
        'NMACK': 1,
        'MACs': 5,
        'sequence': [['00S', '00E', '00E', '12S', '00E'], ['00S', '00E', '00E', '12S', '04S']]
    },
    {
        'ID': 32,
        'sections': 2,
        'NMACK': 1,
        'MACs': 10,
        'sequence': [['00S', '00E', '00G', '00S', '00G', '05S', '12S', '00E', '12E', '00E'],
                     ['00S', '00G', '00E', '00G', '05S', '00S', '05E', '04S', '12S', '00E']]
    },
    {
        'ID': 33,
        'sections': 2,
        'NMACK': 1,
        'MACs': 6,
        'sequence': [['00S', '00E', '04S', '00E', '12S', '00E'], ['00S', '00E', '00E', '12S', '00E', '12E']]
    },
    {
        'ID': 34,
        'sections': 2,
        'NMACK': 1,
        'MACs': 6,
        'sequence': [['00S', 'FLX', '04S', 'FLX', '12S', '00E'], ['00S', 'FLX', '00E', '12S', '00E', '12E']]
    },
]
