[![ICD 1.0 Test Vectors](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_test_vectors.yml/badge.svg?branch=OSNMA_ICD_1.0)](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_test_vectors.yml)
[![ICD 1.0 Corner Cases](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_corner_cases.yml/badge.svg)](https://github.com/Algafix/OSNMA/actions/workflows/icd_10_corner_cases.yml)

OSNMAlib
========

### **NOTE:** This branch implements the new ICD 1.0 transmitted live since 2023-08-03 11:00. It will be a branch until test vectors are released for this new ICD, then master and this branch will be swapped.

### **NOTE:** While there are some corner cases not yet implemented, this branch should work correctly with the new ICD data in the majority of situations. The run folders contain the current Public Key and Merkle Tree root.


OSNMAlib is an open-source Python library that can be integrated into existing receivers and applications to incorporate 
navigation message authentication to the positioning process. It can read the Galileo I/NAV pages when received, store 
the navigation and authentication data, perform the authentication verification, and report the status.

Supports Python 3.8, 3.9 and 3.10+. Tested on Linux and Windows.

Features
---

Current OSNMA ICD **features supported**:

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
  * Support for the following events: EOC, NPK, PKREV, OAM.
    * Missing data to validate the CREV event.
  
**Extra optimizations** for a faster TTFAF:
  * Reconstruct broken HKROOT messages.
  * Reconstruct TESLA key from partial MACK messages.
  * Extract non-FLX tags from broken MACK messages.

Current data **format supported**:

  * Septentrio Binary Format (SBF) log files.
  * Live connection to a Septentrio Receiver through IP port.
  * Live aggregated data from the [galmon](https://github.com/berthubert/galmon) project.
  * Allows for custom data by implementing your iterator.

Future development:

  * Renew Merkle Tree procedure
  * IDD ICD implementation for authentication of cryptographic materials.
  * Time synchronization options.

Documentation
---

NAVITEC Conference on OSNMAlib
  * [OSNMAlib Paper](OSNMAlib_NAVITEC2022.pdf)
  * [Youtube Presentation](https://www.youtube.com/watch?v=IVPzVM5GdKs)

General OSNMA documentation
  * [GSC website with the reference documents](https://www.gsc-europa.eu/electronic-library/programme-reference-documents)
  * Look both at the ICD and the Receiver Guidelines
 

Quick Run - Try it!
===

Requirements
---

The required python libraries can all be installed with `pip` usin the `requirements.txt` file.

```
$ pip install -r requirements.txt
```

Current configuration
---

The folder `custom_run/` contains the current Merkle Tree and Public Key, both downloaded form the official [GSC](https://www.gsc-europa.eu/) website. It also contains the `current_config.sbf` file with the current configuration recorded by me. You can run it directly with the console with:

```
$ cd custom_run/
$ python run.py
```

**Beware** the console output will be huge, you can limit it in the configuration dictionary. A log folder will be created with the same logs for easy parsing.

You can also run your own SBF files (if they contain the GALRawINAV block) by giving it the same name or passing the file as parameter. Mind to also update the Merkle Tree and Public Key files accordingly.

```
$ cd custom_run/
$ python run.py [filename]
```

Real time execution with data from Galmon
---

If you want to see the library process data in real time but don't have a receiver, I've integrated OSNMAlib with the [galmon](https://github.com/berthubert/galmon) project. You can find a  under the folder `live_galmon_run/` and run it:

```
$ live_galmon_run/
$ python run.py
```

You will see information printed about every 30s approximately. There may be some sync problems with the galmon data.

The IP and Port are defaulted to `86.82.68.237:10000`. You can specify your own in the Galmon input class constructor.

Real time execution with a Septentrio receiver
---

If you have access to a Septentrio receiver SBF log output, I have implemented a real time input module for that. To tell the receiver to output the required navigation data send the following commands to it. Mind that `Stream2` or port `20000` may be in use. 

```
setSBFOutput, Stream2, IPS1, GALRawINAV, sec1
setIPServerSettings, IPS1, 20000
```

Then just execute the software. By default it connects to `192.168.3.1:20000`.

```
$ live_septentrio_run/
$ python run.py
```


Execution with Custom Data
===

The OSNMA Open Implementation receiver can be used with custom data files. However, the receiver is only guaranteed to work with data consistent with the OSNMA SIS ICD issue 1.0.

Septentrio Binary Format (SBF)
---

If the custom navigation data is available in Septentrio Binary Format (SBF), the receiver already includes the input 
iterator `SBF` to handle it. The SBF file used needs to contain the block with the raw Galileo INAV bits (GALRawINAV)
so OSNMAlib can process them.

We are also including the iterator `SBFAscii` for the cases where the GALRawINAV
data is in SBF ascii mode (converted from an SBF file using the official tools).

Both can be found [here](https://github.com/Algafix/OSNMA/blob/master/osnma/input_formats/input_sbf.py).

Custom format
---

If the format of the custom data is not supported by OSNMAlib, a new input iterator should be developed following
the instructions on the [Input Data wiki page](https://github.com/Algafix/OSNMA/wiki/Input-Data).


Receiver Options
---

The receiver has several configuration parameters that should be defined previous to execution. Those parameters can be 
specified within code in a Python dictionary or in a separate JSON File and served as an input parameter to the 
receiver. The receiver will load default values for the configuration parameters not specified.

The most important parameters are:

* `scenario_path`: Path to the scenario data file.
* `exec_path`: Path to the folder where the receiver will search for the Merkle Tree root, Public Key and KROOT files, and where will store the keys and the logs (if no log path is specified).
* `merkle_name`: Name of the Merkle Tree root file. Shall be in the GSA XML format.
* `pubkey_name`: Name of the stored Public Key file. Shall be in the GSA XML format.

For a full description see the wiki page [Receiver Options [TBC]](https://github.com/Algafix/OSNMA/wiki/Receiver-Options-%5BTBC%5D).


Support
===

If you are having issues, please use the Issues page in GitHub.

Contribution
===

If you want a protocol to be supported as an input for OSNMAlib you can kindly request it in the GitHub Issues page, providing its documentation and possible ways to test it.

Or you can create a Pull Request with your implementation. I will help you with any question that you may have about the interface class.

License
===

The project is licensed under the EUPL.

About
===

The research leading to this work has been supported by European Commission contract SI2.823546/9 and by the Spanish Ministry of Science and Innovation project PID2020-118984GB-I00. 

Disclaimer
===

OSNMAlib has not been developed or tested operationally. OSNMAlib users use it at their own risk, without any guarantee or liability from the code authors or the Galileo OSNMA signal provider.

OSNMAlib is not affiliated with any private company.
