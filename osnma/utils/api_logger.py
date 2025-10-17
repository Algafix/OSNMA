######## type annotations ########
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from osnma.receiver.satellite import Satellite
    from osnma.cryptographic.gst_class import GST

### imports ###
import json

from osnma.utils.config import Config

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)

SUBFRAMES_IN_MEMORY = 12
"""12 subrames allow for at least one ADKD12 verification in memory"""

class APIBitsLogger:

    def __init__(self):
        self.last_subframes_bits = []

    def _format_subframe_bits(self, satellites: dict[int, 'Satellite']) -> dict:
        """
        Filters to use only current subframe active satellites
        """
        subframe_bits = {}
        for satellite in satellites.values():
            if satellite.is_active():
                subframe_bits[satellite.svid] = satellite.pages_bits_log
        return subframe_bits

    def _add_subframe_bits_to_list(self, gst: 'GST', subframe_bits: dict):
        """
        Inserts the last subframe bits at the beginning of the list and pops the last one if needed
        """
        self.last_subframes_bits.insert(0, {"WN": gst.wn, "TOW": gst.tow, "svid_bits": subframe_bits})
        if len(self.last_subframes_bits) > SUBFRAMES_IN_MEMORY:
            self.last_subframes_bits.pop(-1)

    def do_api_bits_logging(self, gst: 'GST', satellites: dict[int, 'Satellite']):
        """
        Extracts bits for the subframe, saves them with the last subframes and logs to file specified in config
        """
        subframe_bits = self._format_subframe_bits(satellites)
        self._add_subframe_bits_to_list(gst, subframe_bits)
        with open(Config.API_SUBFRAME_BITS_FILE, 'w') as fp:
            json.dump(self.last_subframes_bits, fp)

class APISubframeLogger:

    def __init__(self):
        self.last_subframes_json = []

    def do_api_subframe_logging(self, subframe_status_dict: dict):
        self.last_subframes_json.insert(0, subframe_status_dict)
        if len(self.last_subframes_json) > SUBFRAMES_IN_MEMORY:
            self.last_subframes_json.pop(-1)
        with open(Config.API_SUBFRAME_STATUS_FILE, 'w') as fp:
            json.dump(self.last_subframes_json, fp)
