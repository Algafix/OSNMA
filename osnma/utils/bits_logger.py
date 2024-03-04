######## type annotations ########
from typing import TYPE_CHECKING, Dict
if TYPE_CHECKING:
    from osnma.receiver.receiver import OSNMAReceiver
    from osnma.receiver.satellite import Satellite
    from osnma.cryptographic.gst_class import GST

### imports ###
import pprint
import json

from osnma.utils.config import Config

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)

class BitsLogger:

    def __init__(self):
        self.last_subframes_bits = []

    def _generate_subframe_bits(self, satellites: Dict[int, 'Satellite'] ):
        subframe_bits = {}
        for satellite in satellites.values():
            if satellite.is_active():
                subframe_bits[satellite.svid] = satellite.pages_bits_log
        return subframe_bits

    def _add_subframe_to_dict(self, gst: 'GST', subframe_bits: Dict):
        self.last_subframes_bits.insert(0, {"WN": gst.wn, "TOW": gst.tow, "svid_bits": subframe_bits})

        if len(self.last_subframes_bits) > 10:
            self.last_subframes_bits.pop(-1)

    def do_bits_log(self, gst: 'GST', satellites: Dict[int, 'Satellite']):

        subframe_bits = self._generate_subframe_bits(satellites)
        self._add_subframe_to_dict(gst, subframe_bits)

        with open(Config.SUBFRAME_BITS_FILE, "w") as fp:
            json.dump(self.last_subframes_bits, fp)
