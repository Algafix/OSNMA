[![ICD 1.0 Test Vectors](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_test_vectors.yml/badge.svg)](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_test_vectors.yml)
[![ICD 1.0 Corner Cases](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_corner_cases.yml/badge.svg)](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_corner_cases.yml)

OSNMAlib
========

OSNMAlib is an open-source Python library that can be used for research purposes or be integrated into existing receivers and applications to incorporate navigation message authentication to the positioning process.
It can read the Galileo I/NAV pages from an input, store the navigation and authentication data, perform the verification operations, and report the status.

The software has been successfully tested using the official ICD test vectors and data from corner cases recorded by me. To our knowledge, it has also been used to verify other third-party OSNMA implementations and in research. 

Note that the security of the OSNMA protocol can only be guaranteed if the receiver providing the navigation data is synchronized with TL seconds of error with the Galileo System Time.
By default, OSNMAlib assumes a TL of 30s: the maximum to process all tags. However, it can be configured for a different TL depending on what your receiver can guarantee.
For more information about time synchronisation see the [OSNMA Receiver Guidelines](https://www.gsc-europa.eu/sites/default/files/sites/all/files/Galileo_OSNMA_Receiver_Guidelines_v1.1.pdf), and [Configuration Options](#osnmalib-configuration-options) to configure OSNMAlib.

OSNMAlib implements several optimizations in the cryptographic material extraction and in the process of linking navigation data to tags [[link](https://arxiv.org/abs/2403.14739)].
None of these optimizations imply trial-and-error on the verification process, so if you see authentication failures in 
a non-spoofing scenario, feel free to report them. 

A live visualization of the output of OSNMAlib can be found at [OSNMAlib.eu](https://osnmalib.eu/).
This web view uses a receiver located in KU Leuven, Belgium, and live aggregated data from [galmon](https://github.com/berthubert/galmon),
to display the general state of OSNMA. It also provides the raw navigation bits received in json format.

If you are using data from the OSNMA Test Phase (before 2023-08-03 11:00), use the [OSNMA_Test_Phase_ICD branch](https://github.com/Algafix/OSNMA/tree/OSNMA_Test_Phase_ICD).

Supports Python 3.8, 3.9, 3.10, and 3.11. Tested on Linux and Windows.

Features
---

Current OSNMA ICD **features supported**:

  * Verification of the public key retrieved from the DSM-PKR message.
  * Verification of the TESLA root key retrieved from the DSM-KROOT message.
  * Verification of a TESLA key against a root key or a previously authenticated key.
  * Verification of the MACK message structure:
    * ADKD sequence.
    * MACSEQ value.
    * FLX tags.
  * Verification of the ADKD 0, ADKD 4 and ADKD 12 tags.
  * Authentication of the navigation data.
  * Support for custom TL values.
  * Support for Cold Start, Warm Start and Hot Start.
  * Support for the following events: EOC, CREV, NPK, PKREV, NMT, and OAM.
  
**Extra optimizations** for a faster TTFAF:
  * Reconstruct broken HKROOT messages.
  * Reconstruct TESLA key from partial MACK messages.
  * Extract valid tags from broken MACK messages.
  * Link and recover lost data using the IOD and the COP.
    * Obtain TTFAF as low as 44 seconds in hot start.
    * https://arxiv.org/abs/2403.14739

Current data [formats supported](https://github.com/Algafix/OSNMA/wiki/Input-Data):

  * Septentrio Binary Format (SBF) log files.
  * Septentrio receiver live connection through IP port.
  * u-blox UBX log files
  * u-blox live connection through COM port 
  * Live aggregated data from the [galmon](https://github.com/berthubert/galmon) project.
  * [GNSS-SDR](https://gnss-sdr.org/) project format through UDP socket
  * Allows for custom data by implementing your iterator.

Future development:

  * Standard JSON output for monitoring
  * Time synchronization options for live execution.
  * IDD ICD implementation for authentication of cryptographic materials.

Documentation
---

OSNMAlib
  * This README file.
  * [Wiki](https://github.com/Algafix/OSNMA/wiki)
  * [OSNMAlib Paper ICL-GNSS 2024](OSNMAlib_ICL_GNSS_2024.pdf)
  * [OSNMAlib Paper NAVITEC 2022 (old)](OSNMAlib_NAVITEC2022.pdf)
  * See later in the README for a list of publications using OSNMAlib.

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

The folder `custom_run/` contains the current Merkle Tree and Public Key, both downloaded from the official [GSC](https://www.gsc-europa.eu/) website. It also contains the `current_config.sbf` file with the current configuration recorded by me. You can run it directly with the console with:

```
$ cd custom_run/
$ python run.py
```

**Beware** the console output will be huge, you can limit it in the configuration dictionary. A log folder will be created with the same logs for easy parsing.

You can also run your own SBF files (if they contain the GALRawINAV block) by giving it the same name or passing the file as parameter. Mind to also update the Merkle Tree and Public Key files if they contain old data.

```
$ cd custom_run/
$ python run.py [filename]
```

Real-time execution with data from Galmon
---

If you want to see the library process data in real-time but don't have a receiver, I've integrated OSNMAlib with the [galmon](https://github.com/berthubert/galmon) project. You can find it under the folder `live_galmon_run/` and run it with:

```
$ cd live_galmon_run/
$ python run.py
```

You will see information printed about every 30s approximately.
There may be some problems with the data received from galmon due to the P2P nature of this service.

The IP and Port are defaulted to `86.82.68.237:10000`. You can specify your own in the Galmon input class constructor.

Real-time execution with a Septentrio receiver
---

If you have access to a Septentrio receiver SBF log output, I have implemented a real-time input module for that. To tell the receiver to output the required navigation data send the following commands to it. Mind that `Stream2` or port `20000` may be in use. 

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

The tests can also be executed using the traditional Python interpreter. In that case, the following shell commands 
should be executed.

```
$ pip install -r requirements.txt
$ cd tests
$ python3 icd_test_vectors.py 
# or
$ python3 test_corner_cases.py 
```

OSNMAlib Configuration Options
===

OSNMAlib has several configuration parameters that can be defined previous to execution. The parameters are defined in a dictionary and sent to the receiver when creating the receiver object.
Note that you can create a script to read the parameters from a JSON and send it to the receiver.
The receiver will load default values for the configuration parameters not specified.

The most important parameters are:
* `exec_path [mandatory]`: Path to the folder where OSNMAlib will search for the Merkle Tree root, Public Key and KROOT. OSNMAlib will also store the received cryptographic material and logs (if no log path is specified).
* `merkle_name [default='OSNMA_MerkleTree.xml']`: Name of the Merkle Tree root file. Shall be in the GSA XML format.
* `pubkey_name [default='']`: Name of the stored Public Key file. If nothing is specified, OSNMAlib will assume Cold Start. Shall be in the GSA XML format.
* `kroot_name [default='']`: Name of the stored KROOT file. Shall have one line with the DSM KROOT complete message in hexadecimal and another line with the NMA Header in hexadecimal.
* `TL [default=30]`: Time synchronization value [s] of the receiver with the Galileo Satellite System time.

Based on the cryptographic material provided to OSNMAlib in the configuration dictionary, it will be set in one of the 3 start states defined in the ICD.
* **Cold Start**: OSNMAlib has no Public Key saved, it needs to be retrieved from the OSNMA message.
* **Warm Start**: OSNMAlib has a Public Key saved and verified, but it is missing the Tesla KROOT. It needs to be retrieved from the OSNMA message.
* **Hot Start**: OSNMAlib has a Public Key and a Tesla KROOT saved and verified, but it needs to be sure the KROOT is still useful.

For a full description of the parameters and a diagram of the starting sequence, see the wiki page [OSNMAlib Configuration Options](https://github.com/Algafix/OSNMA/wiki/OSNMAlib-Configuration-Options).

OSNMAlib Logging Options
---

There are two logging modalities (verbose and status) and two logging destinations (console and file) that can be enabled independently.

The **verbose** log outputs everything meaningful that happens in OSNMAlib in a time-sorted way.
This means that OSNMAlib processes the data from the input and outputs what has managed to do with this data before
reading the next.

The **status** log, on the other hand, outputs information only at the end of a subframe. This logging modality can be useful
to see the current state of OSNMAlib without having to scroll and get overwhelmed by it.

When enabling the console as logging destination, both logging modalities are merged in the console output.
However, if you enable the file logging, a file is created for each modality.
Finally, there is a beta logging mode that always outputs the last subframe status in JSON format to a file.

For more information on how to set these logging options, see the wiki page [OSNMAlib Configuration Options](https://github.com/Algafix/OSNMA/wiki/OSNMAlib-Configuration-Options).

Research Notice
===

This repository partially contains data, information, and ideas regarding an ongoing PhD research.
Please do not plagiarize OSNMA ideas and optimizations read on this repository until they have been scientifically disclosed, so you can reference them.

I strongly believe in open-source software and free access to knowledge, and this whole project remains open to honour these ideals.

However, this approach by my side requires the uttermost respect to the research integrity and ethics by anyone accessing the repository. 

Publication list:
* "OSNMAlib: An Open Python Library for Galileo OSNMA," _NAVITEC_, Noordwijk, Netherlands, 2022. [[link](https://ieeexplore.ieee.org/document/9847548)]
  * Some sections are a bit outdated.
* "Improving Galileo OSNMA Time To First Authenticated Fix." _arXiv preprint_ arXiv:2403.14739, 2024. [[link](https://arxiv.org/abs/2403.14739)]
  * This work has been submitted to the IEEE for possible publication.
* "GNSS Recordings for Galileo OSNMA Evaluation", _IEEE Dataport_, 2024. [[link](https://dx.doi.org/10.21227/a0nm-kn45)]
  * Dataset used for the "Improving Galileo OSNMA Time To First Authenticated Fix" manuscript.
* "OSNMAlib Improvements and Real-Time Monitoring of Galileo OSNMA," _ICL-GNSS_, 2024.
  * Will be linked after the conference takes place.

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

This research is partially funded by the Research Foundation Flanders (FWO) Frank de Winne PhD Fellowship, project number 1SH9424N.

Disclaimer
===

OSNMAlib has not been developed or tested operationally. OSNMAlib users use it at their own risk, without any guarantee or liability from the code authors or the Galileo OSNMA signal provider.

OSNMAlib is not under any private company.
