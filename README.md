[![Python 3.8](https://github.com/Algafix/OSNMA/actions/workflows/tests_python_38.yml/badge.svg)](https://github.com/Algafix/OSNMA/actions/workflows/tests_python_38.yml)
[![Python 3.9](https://github.com/Algafix/OSNMA/actions/workflows/tests_python_39.yml/badge.svg)](https://github.com/Algafix/OSNMA/actions/workflows/tests_python_39.yml)
[![Python 3.10](https://github.com/Algafix/OSNMA/actions/workflows/tests_python_310.yml/badge.svg)](https://github.com/Algafix/OSNMA/actions/workflows/tests_python_310.yml)

OSNMAlib
========

OSNMAlib is an open source Python library that can be integrated in existing receivers and applications to incorporate 
navigation message authentication to the positioning process. It can read the Galileo I/NAV pages when received, store 
the navigation and authentication data, perform the authentication verification, and report the status.

Supports Python 3.8, 3.9 and 3.10. Tested on Linux and Windows.

Features
---

Currently supported:

  * Verification of the public key retrieved from the DSM-PKR message.
  * Verification of the TESLA root key retrieved from the DSM-KROOT message (all algorithms).
  * Verification of a TESLA key against a root key or a previously authenticated key.
  * Verification of the MACK message structure:
    * ADKD sequence.
    * MACSEQ value.
    * FLX tags.
  * Verification of the ADKD 0, ADKD 4 and ADKD 12 tags.
  * Authentication of the navigation data.
  * Support for Cold Start, Warm Start and Hot Start.
  * Support for the following events: EOC, NPK, PKREV.
    * Missing data to validate the CREV and OAM events.
  * Multiple tests with real recorded data from the 6 configurations of the Internal Test Phase and the current Test Phase configuration (conf 7).

Future development:

  * ~~Support for SBF directly (no conversion to SBF Ascii).~~ Done! Use the SBF input class on osnma/receiver/input_sbf.py file.
  * Development of an input iterator for real-time navigation data.
    * Integration with SBF logging real-time navigation data.
    * Integration with Galmon real-time navigation data.
  * TTFAF metric displayed in the logs.
  * Time synchronization options.

Documentation
---

NAVITEC Conference
  * [OSNMAlib Paper](OSNMAlib_NAVITEC2022.pdf)
  * [Youtube Presentation](https://www.youtube.com/watch?v=IVPzVM5GdKs)
 

Test Execution
===

The software is provided with several test scenarios under the folder `tests/scenarios/`. The scenarios cover 
different configurations and events of the OSNMA protocol. The data used by this tests was recorded on the OSNMA 
Internal and Public Test Phases (2020 - 2022).

To run the test is recommended to use the Python framework `pytest`, although they can be run calling the traditional 
Python interpreter. Keep in mind that this execution may take a few minutes, since each test comprises several hours of satellite data.

By default, all tests are executed with `info` logging level on the file handler. That is, the log files will
contain the maximum amount of information. This log files are stored under the folder `tests/test_logs`.
For each sub-test (in this case, for each scenario) a subfolder is created with the name format `logs_YYYYmmdd_HHMMSS`.

Pytest
---

The `pytest` framework is the easiest way to execute the OSNMA Open Implementation receiver tests. To do so, the 
following shell commands are provided. Note that the users interpreter work directory is assumed to be the top
folder of the provided software and `python pip` shall be already installed.

```
$ pip install -r requirements.txt
$ cd tests
$ pytest receiver_test.py
```

Python interpreter
---

The tests can also be executed using the traditional Python interpreter. In that case, the following shell commands 
should be executed.

```
$ pip install -r requirements.txt
$ cd tests
$ python3 receiver_test.py
```

Execution with Custom Data
===

The OSNMA Open Implementation receiver can be used with custom data files. However, the receiver is only guaranteed to 
work with data consistent with the OSNMA User ICD for the Test Phase version 1.0.


Data Format
---

The receiver works by instantiating an iterator that, for each iteration, returns the iteration index and a `DataFormat`
object. The `DataFormat` class and the different iterators are defined under the Python file `osnma/receiver/input.py`.

In Python, an iterator is an object which implements the iterator protocol, which consist of the methods 
`__iter__()` and `__next__()`. The `__iter__()` method allows to do some initializing, but must always return the 
iterator object itself. The `__next__()` method also allows to do operations, and must return the next item in the 
sequence.

The `DataFormat` object must contain the SVID of the satellite transmitting the navigation data as an `integer`, the
WN and TOW at the start of the navigation data page as an `integer`, and the navigation data bits for a nominal page 
(also called double page) which are 240 bits as a `BitArray` object. The `BitArray` object can be initialized from data
in binary format, hex format, integer or any Python Byte Array objects.

Additionally, the `DataFormat` object will take as parameter the signal frequency band and the CRC status. The only 
signal frequency band supported by the receiver is the E1-B, identified with the string `GAL_L1BC`, if no band is 
specified, the receiver will take that as default. The CRC status is a boolean value that indicated if the page has 
passed the CRC verification, it is set to `True` by default.

### Septentrio Binary Format

If the custom navigation data is available in Septentrio Binary Format (SBF), the receiver already includes the input 
iterator `SBFAscii` to handle it. However, the SBF file should be converted to ASCII readable format with the SBF 
Converter included in the free Septentrio RXTools suite.

To do so, in the SBF Converter software, the conversion option `bin2asc` should be selected.
Then, select only the `GALRawINAV` message and no other option. The generated `.txt` file is a CSV file with comma 
separators and can be directly used by the `SBFAscii` input iterator.

### Custom format

If the custom format of the data is not supported by the receiver, a new input iterator should be developed following
the instructions in Section Data Format. The new input iterator can be forwarded as a parameter to the receiver as any 
of the native input iterators without any difference.


Receiver Options
---

The receiver has several configuration parameters that can be defined previous to execution. Those parameters can be 
specified within code in a Python dictionary or in a separate JSON File and served as an input parameter to the 
receiver. The receiver will load default values for the configuration parameters not specified.

Those configuration parameters are:

* `scenario_path`: Path to the scenario data file.
* `exec_path`: Path to the folder where the receiver will search for the Merkle Tree root, Public Key and KROOT files, and where will store the keys and the logs (if no log path is specified).
* `merkle_name`: Name of the Merkle Tree root file. Shall be in the GSA XML format.
* `pubkey_name`: Name of the stored Public Key file. Shall be in the GSA XML format.
* `kroot_name`: Name of the stored KROOT file. Shall have one line with the DSM KROOT complete message in hexadecimal and another line with the NMA Header in hexadecimal.
* `file_log_level`: Log level for the file logs. Possible values are: `debug`, `info`, `warning`, `error`, and `critical`. Default set to `info`.
* `console_log_level`: Log level for the console logs. Possible values are: `debug`, `info`, `warning`, `error`, and `critical`. Default set to `debug`.
* `log_console`: Boolean value indicating if the receiver should log to console. Default set to `True`.
* `logs_path`: Path to the folder where the logs will be saved. It defaults to the same folder as the {exec\_path`.
* `sync_source`: Source used to perform the synchronization check. Possible values are: 0 (subframe time), 1 (user defined time), 2 (NTP), 3 (RTC). Default set to 0.
* `sync_time`: If the synchronization source is set to user defined, this will be the UTC time used.
* `tl`: Loose time synchronization requirement for a secure TESLA protocol initialization. Default to 30 seconds.
* `b`: Maximum error of time reference at the beginning of the 1st bit of information from the file. Default to [TBD].
* `ns`: Number of satellites in the Galileo constellation. Default to 36 satellites. 
* `tag_length`: Number of bits from verified tags to accumulate to consider the corespondent data authenticated. Default set to 80 bits.


Support
===

If you are having issues, please use the Issue page in GitHub.

License
===

The project is licensed under the EUPL.

About
===

The research leading to this work has been supported by European Commission contract SI2.823546/9 and by the Spanish Ministry of Science and Innovation project PID2020-118984GB-I00. 

Disclaimer
===

OSNMAlib has not been developed or tested operationally. OSNMAlib users use it at their own risk, without any guarantee or liability from the code authors or the Galileo OSNMA signal provider.

