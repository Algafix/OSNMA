[![ICD 1.0 Test Vectors](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_test_vectors.yml/badge.svg)](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_test_vectors.yml)
[![ICD 1.0 Corner Cases](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_corner_cases.yml/badge.svg)](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_corner_cases.yml)

OSNMAlib
========

OSNMAlib is an open-source Python library that can be used for research purposes or be integrated into existing receivers and applications to incorporate navigation message authentication to the positioning process.
It can read the Galileo I/NAV pages from an input, store the navigation and authentication data, perform the verification operations, and report the status.

The software has been successfully tested using the official ICD test vectors and data from corner cases recorded by us. To our knowledge, it has also been used to verify other third-party OSNMA implementations and in research. 

Note that the security of the OSNMA protocol can only be guaranteed if the receiver providing the navigation data is synchronized with TL seconds of error with the Galileo System Time.
By default, OSNMAlib assumes a TL of 30s: the maximum to process all tags. However, it can be configured for a different TL depending on what your receiver can guarantee.
For more information about time synchronisation see the [OSNMA Receiver Guidelines](https://www.gsc-europa.eu/sites/default/files/sites/all/files/Galileo_OSNMA_Receiver_Guidelines_v1.3.pdf), and [Configuration Options](#osnmalib-configuration-options) to configure OSNMAlib.

OSNMAlib implements several optimizations in the cryptographic material extraction and in the process of linking navigation data to tags [[link](https://arxiv.org/abs/2403.14739)].
None of these optimizations imply trial-and-error on the verification process, so if you see authentication failures in 
a non-spoofing scenario, feel free to report them. 

A live visualization of the output of OSNMAlib can be found at [OSNMAlib.eu](https://osnmalib.eu/).
This web view uses a receiver located in KU Leuven, Belgium, and live aggregated data from [galmon](https://github.com/berthubert/galmon),
to display the general state of OSNMA. It also provides the [raw navigation bits](https://osnmalib.eu/septentrio/subframe_bits) received and the [OSNMAlib status](https://osnmalib.eu/septentrio/subframe_json) in JSON format.

If you are using data from the OSNMA Test Phase (before 2023-08-03 11:00), use the [OSNMA_Test_Phase_ICD branch](https://github.com/Algafix/OSNMA/tree/OSNMA_Test_Phase_ICD).

Supports Python 3.10, 3.11 and 3.12. For older Python versions, check the branches. Tested on Linux and Windows.

OSNMAlib Features
---

### Features supported:

  * Verification of the public key retrieved from the DSM-PKR message.
  * Verification of the TESLA root key retrieved from the DSM-KROOT message.
  * Verification of a TESLA key against a root key or a previously authenticated key.
  * Verification of the MACK message structure:
    * ADKD sequence.
    * MACSEQ value.
    * FLX tags.
  * Verification of the ADKD 0, ADKD 4 and ADKD 12 tags.
  * Authentication of the navigation data.
  * Support for custom Time Synchronization values.
  * Support for Cold Start, Warm Start and Hot Start.
  * Support for the following events: EOC, CREV, NPK, PKREV, NMT, and OAM.
  * [JSON output](#osnmalib-logging-options) for monitoring and postprocessing with `json-schema` [[html](https://osnmalib.eu/json-schema)|[json](osnma/utils/json_schema/status_log_schema.json)].
  * Report the Time To First Authenticated Fix (TTFAF) and Time To First Fix (TTFF) in terms of navigation data.  

### Extra optimizations for a faster TTFAF:
  * Reconstruct broken HKROOT messages.
  * Reconstruct TESLA key from partial MACK messages.
  * Extract valid tags from broken MACK messages.
  * Reed-Solomon recovery of I/NAV data using word types 17 to 20.
  * Dual frequency reception of I/NAV data from the E5b-I signal.
  * Link and recover lost data using the IOD and the COP.
    * Obtain TTFAF as low as 44 seconds in hot start.
    * IEEE TAES article: [accepted](papers/OSNMA_TTFAF_TAES_2025.pdf) version, [published](https://ieeexplore.ieee.org/document/11004420) version.

### Current [input formats](https://github.com/Algafix/OSNMA/wiki/Input-Data) supported:

  * Septentrio Binary Format (SBF) log files.
  * Septentrio receiver live connection through IP port.
  * u-blox UBX log files.
  * u-blox live connection through COM port.
  * Live aggregated data from the [galmon](https://github.com/berthubert/galmon) project.
  * Android [GNSSLogger App](https://play.google.com/store/apps/details?id=com.google.android.apps.location.gps.gnsslogger) files in postprocess (contact me if you are interested in live data).
  * [GNSS-SDR](https://gnss-sdr.org/) project format through UDP socket.
    * Note that GNSS-SDR [recently implemented OSNMA](https://gnss-sdr.org/osnma/) inside their GNSS receiver.
  * Allows for custom data by implementing your iterator.

### Future development:

  * Time synchronization options for live execution.
  * IDD ICD implementation for authentication of cryptographic materials.

Documentation
---

OSNMAlib
  * This README file.
  * [Wiki](https://github.com/Algafix/OSNMA/wiki)
  * OSNMAlib Journal Paper IEEE JISPN - [[local]](papers/OSNMAlib_JOURNAL_ICL_GNSS_2024_EXPANDED.pdf) - [[online]](https://ieeexplore.ieee.org/document/10955685)
  * OSNMAlib Conference Paper NAVITEC 2022 (outdated) - [[local]](papers/OSNMAlib_NAVITEC2022.pdf) - [[online]](https://ieeexplore.ieee.org/document/9847548)
  * See later in the README for a complete list of publications using OSNMAlib.

General OSNMA documentation
  * [GSC website with the reference documents](https://www.gsc-europa.eu/electronic-library/programme-reference-documents)
  * Look at the ICD, the Receiver Guidelines, and the IDD
 

Quick Run - Try it!
===

Requirements
---

The required Python libraries can all be installed with `pip` using the `requirements.txt` file.

```
$ pip install -r requirements.txt
```

Current configuration
---

The folder `custom_run/` contains the current Merkle Tree and Public Key, both downloaded from the official [GSC](https://www.gsc-europa.eu/) website.
It also contains the `current_config.sbf` file with the current configuration recorded by me. You can run it directly with the console with:

```
$ cd custom_run/
$ python run.py
```

**Beware** the console output will be huge. A log folder will be created with the same logs for easy parsing.

The `run.py` file contains a dictionary with the configuration parameters that are more useful for a normal user.
The parameters are set to their default value, feel free to modify them at will.

You can also run your own SBF files by passing the file name as parameter.
Mind to also update the Merkle Tree and Public Key files in the configuration dictionary of `run.py` appropriately.

```
$ cd custom_run/
$ python run.py [filename]
```

Real-time execution with data from Galmon
---

If you want to see the library process data in real-time but don't have a receiver, I've integrated OSNMAlib with the [galmon](https://github.com/berthubert/galmon) project.
You can find it under the folder `live_galmon_run/` and run it with:

```
$ cd live_galmon_run/
$ python run.py
```

You will see information printed every 30s approximately.
There may be some problems with the data received from galmon due to the P2P nature of this service.

The IP and Port are defaulted to `86.82.68.237:10000`. You can specify your own in the Galmon input class constructor.

Real-time execution with a Septentrio receiver
---

If you have access to a Septentrio receiver SBF log output, I have implemented a real-time input module for that.
To tell the receiver to output the required navigation data send the following commands to it. Mind that `Stream2` or port `20000` may be in use. 

```
setSBFOutput, Stream2, IPS1, GALRawINAV, sec1
setIPServerSettings, IPS1, 20000
```

Then just execute the software. By default, it connects to `192.168.3.1:20000`.

```
$ cd live_septentrio_run/
$ python run.py
```

Other input formats
---

The wiki page [Input Data](https://github.com/Algafix/OSNMA/wiki/Input-Data) contains useful information
about all the input formats supported by OSNMAlib as well as documentation on how to develop a new one.

Test Execution
===

The software is provided with several test scenarios under the folder `tests/scenarios/`.
The scenarios cover different configurations and events of the OSNMA protocol.
The test files come from the Official Test Vectors and also from the live recording of some corner cases.

The `pytest` framework is the easiest way to execute the OSNMA Open Implementation receiver tests. To do so, the 
following shell commands are provided. Note that the users interpreter work directory is assumed to be the top
folder of the provided software and `python pip` shall be already installed.

```
$ pip install -r requirements.txt
$ cd tests
$ pytest icd_test_vectors.py 
# or
$ pytest test_corner_cases.py 
```

The tests can also be executed using the traditional Python interpreter.
In that case, execute the following shell commands.

```
$ pip install -r requirements.txt
$ cd tests
$ python3 icd_test_vectors.py 
# or
$ python3 test_corner_cases.py 
```

OSNMAlib Configuration Options
===

OSNMAlib has several configuration parameters that can be defined previous to execution.
The parameters are defined in a dictionary and passed to the receiver when creating the receiver object.
The receiver will load default values for the configuration parameters not specified.

The most important parameters are:
* `exec_path [mandatory]`: Path to the folder where OSNMAlib will search for the Merkle Tree root, Public Key and KROOT. OSNMAlib will also store the received cryptographic material and logs (if no log path is specified).
* `merkle_name [default='OSNMA_MerkleTree.xml']`: Name of the Merkle Tree root file. Shall be in the GSA XML format.
* `pubkey_name [default='']`: Name of the stored Public Key file. If nothing is specified, OSNMAlib will assume Cold Start. Shall be in the GSA XML format.
* `kroot_name [default='']`: Name of the stored KROOT file. Shall have one line with the DSM KROOT complete message in hexadecimal and another line with the NMA Header in hexadecimal.
* `TL [default=30]`: Time synchronization value [s] of the receiver with the Galileo Satellite System time.

Based on the cryptographic material provided to OSNMAlib in the configuration dictionary, it will be set in one of the 3 start states defined in the ICD.
* **Cold Start**: OSNMAlib has no Public Key saved, it needs to be retrieved from the OSNMA message.
* **Warm Start**: OSNMAlib has a Public Key saved, but it is missing the Tesla KROOT. It needs to be retrieved from the OSNMA message.
* **Hot Start**: OSNMAlib has a Public Key and a Tesla KROOT saved, but it needs to ensure the KROOT is still valid by verifying one TESLA Key.

For a full description of the parameters and a diagram of the starting sequence, see the wiki page [OSNMAlib Configuration Options](https://github.com/Algafix/OSNMA/wiki/OSNMAlib-Configuration-Options).

OSNMAlib Logging Options
---

There are two logging modalities (verbose and status) and two logging destinations (console and file) that can be enabled independently.

The **verbose** log outputs everything meaningful that happens in OSNMAlib in a time-sorted way.
This means that OSNMAlib processes the data from the input and outputs what has managed to do with this data before
reading the next.

The **status** log, on the other hand, outputs information only at the end of a subframe in JSON format.
This logging modality is useful to see the current state of OSNMAlib and post-process OSNMA information logged in the
JSON file. The description of the JSON structure can be found in the following `json-schema` [[html](https://osnmalib.eu/json-schema)|[json](osnma/utils/json_schema/status_log_schema.json)].   

When enabling the console as logging destination, both logging modalities are merged in the console output.
However, if you enable the file logging, a file is created for each modality.
Finally, there is a logging mode that only outputs the last subframe status in JSON format to a file.

For more information on how to set these logging options, see the wiki page [OSNMAlib Configuration Options](https://github.com/Algafix/OSNMA/wiki/OSNMAlib-Configuration-Options).

Research Notice
===

This repository partially contains data, information, and ideas regarding an ongoing PhD research.
Please do not plagiarize OSNMA ideas and optimizations read on this repository until they have been scientifically disclosed, so you can reference them.

I strongly believe in open-source software and free access to knowledge, and this whole project remains open to honour these ideals.

However, this approach by my side requires the uttermost respect to the research integrity and ethics by anyone accessing the repository. 

Publication list
---

Select the appropriate manuscripts to cite in your research. You will find a local copy of each in the [papers](papers) folder.
Note that the conference paper from 2022 is quite outdated.
I recommend citing the 2025 journal paper if you want to reference OSNMAlib as a whole.

* "Improving OSNMAlib: New Formats, Features, and Monitoring Capabilities," in _IEEE Journal of Indoor and Seamless Positioning and Navigation_, 2025. [[link](https://ieeexplore.ieee.org/document/10955685)]
  * Journal extension of the conference paper to ICL-GNSS 2024 [[link](https://ieeexplore.ieee.org/document/10578487)]
  * Report on the new additions to OSNMAlib: new input formats, JSON logging, [osnmalib.eu](https://osnmalib.eu), Reed-Solomon, dual-frequency...
  * Includes TTFAF benchmark of Reed-Solomon and dual-frequency reception in urban scenarios.
* "Improving Galileo OSNMA Time To First Authenticated Fix," in _IEEE Transactions on Aerospace and Electronic Systems_, 2025. [[link](https://ieeexplore.ieee.org/document/11004420)]
  * Technical description of the optimization to reduce the TTFAF to 44 seconds and testing with live data recording.
* "GNSS Recordings for Galileo OSNMA Evaluation", _IEEE Dataport_, 2024. [[link](https://dx.doi.org/10.21227/a0nm-kn45)]
  * Dataset used for the "Improving Galileo OSNMA Time To First Authenticated Fix" manuscript.
* "OSNMAlib: An Open Python Library for Galileo OSNMA," _NAVITEC_, Noordwijk, Netherlands, 2022. [[link](https://ieeexplore.ieee.org/document/9847548)]
  * Original OSNMAlib paper, some sections are outdated.

In case of any doubt, contact me at aleix.galan[@]kuleuven.be

Thank you.


Support
===

If you are having issues, please use the Issues page in GitHub.

Contribution
===

If you want a protocol to be supported as an input for OSNMAlib you can kindly request it in the GitHub Issues page, providing its documentation and possible ways to test it. 
Or you can create a Pull Request with your implementation. I will help you with any question that you may have about the interface class.

License
===

The project is licensed under the EUPL-1.2 license.

About
===

The research leading to this work was supported by European Commission contract SI2.823546/9 and by the Spanish Ministry of Science and Innovation project PID2020-118984GB-I00. 

The current research is partially funded by the Research Foundation Flanders (FWO) Frank de Winne PhD Fellowship, project number 1SH9424N.

Disclaimer
===

OSNMAlib users use it at their own risk, without any guarantee or liability from the code authors or the Galileo signal provider.

OSNMAlib is not under any private company.
