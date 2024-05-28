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

class FieldLengthNotCorrect(Exception):
    pass


class MissingFieldDSM(Exception):
    pass


class FieldValueNotRecognized(Exception):
    pass


class PublicKeyObjectError(Exception):
    pass


class TeslaKeyVerificationFailed(Exception):
    pass


class MackParsingError(Exception):
    pass


class ReceiverStatusError(Exception):
    pass

class StoppedAtFAF(Exception):
    def __init__(self, message, ttfaf: int, first_tow, faf_tow):
        super().__init__(message)
        self.ttfaf = ttfaf
        self.first_tow = first_tow
        self.faf_tow = faf_tow

class IDDException(Exception):
    pass

class DateException(IDDException):
    template_message = "The {message} is not within its validity period."
    def __init__(self, message):
        super().__init__(self.template_message.format(message = message))

class RevokedException(IDDException):
    template_message = "The {message} has been revoked."
    def __init__(self, message):
        super().__init__(self.template_message.format(message = message))

class IssuerException(IDDException):
    template_message = "The issuer and the subject of the {message} have not matched."
    def __init__(self, message):
        super().__init__(self.template_message.format(message = message))

class VerifyException(IDDException):
    template_message = "The {message} signature is invalid."
    def __init__(self, message):
        super().__init__(self.template_message.format(message = message))