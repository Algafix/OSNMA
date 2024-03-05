######## type annotations ########
from typing import TYPE_CHECKING, Dict
if TYPE_CHECKING:
    from osnma.receiver.satellite import Satellite
    from osnma.cryptographic.gst_class import GST

### imports ###
import json

from osnma.utils.config import Config

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)

class BitsLogger:

    def __init__(self):
        self.last_subframes_bits = []
        self.subframes_in_memory = 12
        """12 subrames allow for at least one ADKD12 verification in memory"""

    def _format_subframe_bits(self, satellites: Dict[int, 'Satellite']) -> Dict:
        """
        Filters to use only current subframe active satellites
        """
        subframe_bits = {}
        for satellite in satellites.values():
            if satellite.is_active():
                subframe_bits[satellite.svid] = satellite.pages_bits_log
        return subframe_bits

    def _add_subframe_to_list(self, gst: 'GST', subframe_bits: Dict):
        """
        Inserts the last subframe bits at the beginning of the list and pops the last one if needed
        """
        self.last_subframes_bits.insert(0, {"WN": gst.wn, "TOW": gst.tow, "svid_bits": subframe_bits})
        if len(self.last_subframes_bits) > self.subframes_in_memory:
            self.last_subframes_bits.pop(-1)

    def do_subframe_bits_log(self, gst: 'GST', satellites: Dict[int, 'Satellite']):
        """
        Extracts bits for the subframe, saves them with the last subframes and logs to file specified in config
        """
        subframe_bits = self._format_subframe_bits(satellites)
        self._add_subframe_to_list(gst, subframe_bits)
        with open(Config.SUBFRAME_BITS_FILE, "w") as fp:
            json.dump(self.last_subframes_bits, fp)
