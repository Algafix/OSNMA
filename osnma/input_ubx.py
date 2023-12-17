from struct                import unpack
from bitstring             import BitArray
from datetime              import datetime
from osnma.input_formats.base_classes import DataFormat, PageIterator
import serial, socket

SYNC              = 0xB5, 0x62
UBX_RXM_SFRBX     = 0x02, 0x13

VALID_WORD_TYPE   = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 17, 18, 19, 20 }
SET_TOW_WORD_TYPE = { 0, 5, 6 }

UBX_TIM_TP        = 0x0D, 0x01

UBX_NAV_TIMEGAL   = 0x01, 0x25
UBX_NAV_TIMEGPS   = 0x01, 0x20
UBX_NAV_TIMEBDS   = 0x01, 0x24
UBX_NAV_TIMEGLO   = 0x01, 0x23
UBX_NAV_TIMEUTC   = 0x01, 0x21

UBX_CLOCK         = { UBX_TIM_TP, UBX_NAV_TIMEGAL, UBX_NAV_TIMEGPS, UBX_NAV_TIMEBDS }

#Assume GALILEO OS ICD order for tow estimation
#for 16 assume the lowest time possible
#from 0,5,6,16 assume lowest time possible to next word_type
#rought estimation enable clock messages (TP, TIMEGAL, ...)
WORDS_ORDER_GAL = {

    2:  {4:2, 7:6, 9:6, 8:8, 10:8, 17:10, 18:10, 19:12, 20:12, 16:14, 1:20, 3:22},
    4:  {7:4, 9:4, 8:6, 10:6, 17:8, 18:8, 19:10, 20:10, 16:12, 1:18, 3:20, 2:28},
    7:  {8:2, 10:2, 17:4, 18:4, 19:6, 20:6, 16:8, 1:14, 3:16, 2:24, 4:26},
    9:  {8:2, 10:2, 17:4, 18:4, 19:6, 20:6, 16:8, 1:14, 3:16, 2:24, 4:26},
    8:  {17:2, 18:2, 19:4, 20:4, 16:6, 1:12, 3:14, 2:22, 4:24, 7:28, 9:28},
    10: {17:2, 18:2, 19:4, 20:4, 16:6, 1:12, 3:14, 2:22, 4:24, 7:28, 9:28},
    17: {19:2, 20:2, 16:4, 1:10, 3:12, 2:20, 4:22, 7:26, 9:26, 8:28, 10:28},
    18: {19:2, 20:2, 16:4, 1:10, 3:12, 2:20, 4:22, 7:26, 9:26, 8:28, 10:28},
    19: {16:2, 1:8, 3:10, 2:18, 4:20, 7:24, 9:24, 8:26, 10:26, 17:28, 18:28},
    20: {16:2, 1:8, 3:10, 2:18, 4:20, 7:24, 9:24, 8:26, 10:26, 17:28, 18:28},
    16: {2:2, 4:4, 7:8, 9:8, 8:10, 10:10, 17:12, 18:12, 19:14, 20:14, 1:6, 3:8},
    1:  {3:2, 16:8, 2:10, 4:12, 7:16, 9:16, 8:18, 10:18, 17:20, 18:20, 19:22, 20:22}, 
    3:  {16:6, 2:8, 4:10, 7:14, 9:14, 8:16, 10:16, 17:18, 18:18, 19:20, 20:20, 1:28},
    0:  {1:2, 3:4, 16:2, 2:4, 4:6, 7:8, 9:8, 8:10, 10:10, 17:12, 18:12, 19:14, 20:14},
    5:  {16:4, 2:6, 4:8, 7:10, 9:10, 8:12, 10:12, 17:14, 18:14, 19:16, 20:16, 1:26, 3:28},
    6:  {7:2, 9:2, 8:4, 10:4, 17:6, 18:6, 19:8, 20:8, 16:10, 1:16, 3:18, 2:26, 4:28}
}
def check_sum(buffer): 
   
    buffer_ck_a, buffer_ck_b = buffer[-2], buffer[-1]
    ck_a, ck_b               = 0, 0

    for el in buffer[:-2]:
        ck_a +=   el;  ck_a &= 0xFF
        ck_b += ck_a;  ck_b &= 0xFF

    return ck_a == buffer_ck_a and ck_b == buffer_ck_b


def parse_header(header):
    clas, cid, length = unpack('<BBH', header)
    return (clas, cid), length


def parse_sfrbx_head(payload):
   
    if payload[6] == 0x01:
        head     = unpack('< 2B 2x B x B x', payload[:8])
        gnss     = head[0]
        svid     = head[1]
        numWords = head[2]  
    
    elif payload[6] == 0x02:
        head     = unpack('< 3B x 3B x', payload[:8])
        gnss     = head[0]
        svid     = head[1]
        numWords = head[3]
    
    else: 
        gnss, numWords, svid  = -1, -1, -1

    return gnss, svid, numWords


def parse_tow_from_inav(word_type, inav):
    
    data_word_odd = (inav[4] >> 14) & 0xffff

    if word_type == 0:
        time = (inav[0] >> 22) & 0x3  

        if time != 2: 
            return -1, -1

        wn   = ( inav[3] >> 18) & 0xfff
        tow  = ((inav[3] >> 14) & 0xf) << 16 | data_word_odd
       
    elif word_type == 5: 
        wn  = (inav[2] >> 9)  & 0xfff
        tow = (inav[3] >> 21) | (inav[2] & 0x1ff) << 11
    
    elif word_type == 6:
        tow = (inav[4] >> 17) & 0x1fff | (inav[3] >> 1) & 0xfe000
        wn  = -1
    
    return tow, wn


def parse_sfrbx(payload):
    
    gnss, svid, numWords = parse_sfrbx_head(payload)
   
    if numWords < 8 or svid < -1 or gnss != 2: 
        return "error"
    
    inav      = unpack(f'< {numWords}L', payload[8:])
    word_type = (inav[0] >> 24) & 0x03f
  
    even           =  inav[0] >> 31
    odd            =  inav[4] >> 31
    page_type_even = (inav[0] >> 30) & 0x01
    page_type_odd  = (inav[4] >> 30) & 0x01

    if even != 0 or odd != 1 or page_type_even != 0 or page_type_odd != 0 or \
       word_type not in VALID_WORD_TYPE: 
        return "error"
    
    return svid, word_type, inav[:8]


def get_bit_array(inav): 
    #remove ubx padding in sfrbx
    inav[3] = inav[3] >> 8
    inav[7] = inav[7] >> 8 
    
    res = ''
    for index, data in enumerate(inav):
        if index in [3, 7]:
            res = res + bin(data)[2:].zfill(24)
        else: 
            res = res + bin(data)[2:].zfill(32)

    return BitArray('0b' + res) 


def get_tow_from_clock(class_id, payload):
  
    if class_id == UBX_TIM_TP:
        clock_parsed = unpack('< 2L l H 2b', payload)
        tow = (clock_parsed[0] // 1000) - 1 
        tow = tow - (3 - tow % 2)
        wn = clock_parsed[3] - 1024

    elif class_id == UBX_NAV_TIMEGAL:
        clock_parsed = unpack('< 2L l h 2b L', payload)
        tow = clock_parsed[1]
        tow = tow - (3 - tow % 2)     
        wn = clock_parsed[3]

    elif class_id == UBX_NAV_TIMEGPS:
        clock_parsed = unpack('< L l h b x L', payload)
        tow = (clock_parsed[0] // 1000) - 1
        tow = tow - (3 - tow % 2)
        wn = clock_parsed[2] - 1024
        
    elif class_id == UBX_NAV_TIMEBDS:
       clock_parsed = unpack('< 2L l h 2b L', payload)
       tow = (clock_parsed[0] // 1000) - 1
       tow = tow - (3 - tow % 2)    
       wn  = clock_parsed[3] + 332

    return tow, wn




class UBX(PageIterator): 
    def __init__(self, path) -> None:
        super().__init__()
        self.file        = open(path, 'br')
        self.file_pos    = self.file.tell()
        self.use_clock   = False
        self.tow = self.wn = 0
        
        self._find_clock()
        
        if not self.use_clock:
            self.tow_word = {}


    def __next__(self): 
        if not self.use_clock: 
            return self.next_without_clock()
        
        return self.next_with_clock()
        

    def _find_clock(self):
        while sync := self.file.read(2):

            if (sync[0], sync[1]) != SYNC: 
                continue

            if  ( header := self.file.read(4) ) == b'':
                break

            class_id, length = parse_header(header)
            _                = header + self.file.read(length + 2) 

            if class_id in UBX_CLOCK:
                self.use_clock = True
                self.file.seek(0, 0)
                break 

    def next_with_clock(self) -> 'DataFormat':
        data_format = None

        while sync := self.file.read(2):
            
            if (sync[0], sync[1]) != SYNC: 
                continue

            if  ( header := self.file.read(4) ) == b'':
                break

            class_id, length = parse_header(header)
            frame            = header + self.file.read(length + 2) 
            is_valid_frame   = check_sum(frame)
            self.file_pos    = self.file.tell()
            payload          = frame[4:-2]

            if is_valid_frame and self.tow > 0 and class_id == UBX_RXM_SFRBX: 
                parsed_sfrbx = parse_sfrbx(payload)

                if parsed_sfrbx == "error":
                    continue

                svid, word_type, inav  = parsed_sfrbx
                bit_array_inav = get_bit_array(list(inav))
                data_format    = DataFormat(svid, self.wn, self.tow, bit_array_inav)
                break

            elif is_valid_frame and class_id in UBX_CLOCK:
                self.tow, self.wn = get_tow_from_clock(class_id, payload)
 
        if data_format is None:
            raise StopIteration
        
        return data_format

    def next_without_clock(self) -> 'DataFormat':

        data_format = None

        while sync := self.file.read(2):
            
            if (sync[0], sync[1]) != SYNC: 
                continue

            if  ( header := self.file.read(4) ) == b'':
                break
            
            class_id, length = parse_header(header)
            frame            = header + self.file.read(length + 2) 
            is_valid_frame   = check_sum(frame)
            self.file_pos    = self.file.tell()
            payload          = frame[4:-2]
            

            if is_valid_frame and class_id == UBX_RXM_SFRBX: 
                parsed_sfrbx = parse_sfrbx(payload)

                if parsed_sfrbx == "error":
                    continue

                svid, word_type, inav  = parsed_sfrbx
                
                if word_type in SET_TOW_WORD_TYPE:
                    if self.wn > 0:  
                        tow, _ = parse_tow_from_inav(word_type, inav)
                    else: 
                        tow, self.wn = parse_tow_from_inav(word_type, inav) 
                    
                    if svid in self.tow_word and tow < self.tow_word[svid][0]:
                        continue
                    
                    self.tow_word[svid] = (tow, word_type)
                else: 
                    if svid not in self.tow_word:
                        continue
                    
                    tow, prev_word_type = self.tow_word[svid]

                    if prev_word_type == word_type:
                        offset = 2
                    else:
                        offset = WORDS_ORDER_GAL[prev_word_type][word_type]
                    self.tow_word[svid] = (tow + offset, word_type)
                
                if self.wn <= 0:
                    continue
                
                bit_array_inav = get_bit_array(list(inav))
                data_format    = DataFormat(svid, self.wn, self.tow_word[svid][0], bit_array_inav)
                break 
        
        if data_format is None:
            raise StopIteration
        
        return data_format


class UBXSerial(PageIterator):
    def __init__(self, port) -> None: 
        super().__init__()
        
        try: 
            self.s = serial.Serial(port, baudrate=115200, timeout=0)
        except: 
            raise ValueError('Port not available')
        
        self.use_clock = False
        self._find_clock()
        
        if not self.use_clock:
            self.__init__without_clock()
            self.datetime = datetime.now()


    def __del__(self):
        self.s.close()

    
    def __next__(self) -> 'DataFormat': 
        if not self.use_clock: 
            return self.next_without_clock()
        
        return self.next_with_clock()

    
    def _find_clock(self): 
        t_end = datetime.now().second + 3
        while datetime.now().second < t_end:

            if not (frame := self.s.read(4096)): 
                continue
                
            if (frame[0], frame[1]) != SYNC: 
                continue

            class_id, _    = parse_header(frame[2:6])
            is_valid_frame = check_sum(frame[2:])

            if is_valid_frame and class_id in UBX_CLOCK:
                self.tow, self.wn = get_tow_from_clock(class_id, frame[6:-2])
                self.use_clock = True
                break
    
    
    def __init__without_clock(self):
        
        while True: 
            if not (frame := self.s.read(4096)): 
                continue
                
            if (frame[0], frame[1]) != SYNC: 
                continue

            class_id, _    = parse_header(frame[2:6])
            is_valid_frame = check_sum(frame[2:])

            if is_valid_frame and class_id == UBX_RXM_SFRBX:
                parsed_sfrbx = parse_sfrbx(frame[6:-2])

                if parsed_sfrbx == "error":
                    continue
                
                _, word_type, inav = parsed_sfrbx
                if word_type in SET_TOW_WORD_TYPE:
                    tow, wn            =  parse_tow_from_inav(word_type, inav)
                    
                    if tow != -1 and wn != -1:
                        self.tow = tow 
                        self.wn  = wn
                        break
    
    
    def next_with_clock(self) -> 'DataFormat': 
        
        data_format = None
        
        while True:
            if not (frame := self.s.read(4096)): 
                continue
                
            if (frame[0], frame[1]) != SYNC: 
                continue

            class_id, _    = parse_header(frame[2:6])
            is_valid_frame = check_sum(frame[2:])

            if is_valid_frame and class_id == UBX_RXM_SFRBX: 
                parsed_sfrbx = parse_sfrbx(frame[6:-2])
                                
                if parsed_sfrbx == "error":
                    continue
                
                svid, word_type, inav = parsed_sfrbx
                
                if word_type in SET_TOW_WORD_TYPE:
                    tow, _ = parse_tow_from_inav(word_type, inav)
                    assert tow == self.tow

                bit_array_inav = get_bit_array(list(inav))
                data_format    = DataFormat(svid, self.wn, self.tow, bit_array_inav)
                break
                
            elif is_valid_frame and class_id in UBX_CLOCK:
                self.tow, self.wn = get_tow_from_clock(class_id, frame[6:-2])
                        
        if data_format is None:
            raise StopIteration
        
        return data_format 
    
    
    def next_without_clock(self) -> 'DataFormat':
        data_format = None
        
        while True:
            if not (frame := self.s.read(4096)): 
                continue

            if (frame[0], frame[1]) != SYNC: 
                continue

            class_id, _    = parse_header(frame[2:6])
            is_valid_frame = check_sum(frame[2:])

            if is_valid_frame and class_id == UBX_RXM_SFRBX: 
                parsed_sfrbx = parse_sfrbx(frame[6:-2])

                if parsed_sfrbx == "error":
                    continue
                
                time_now = datetime.now() 
                seconds = round((time_now - self.datetime).total_seconds())
                
                if seconds > 0:
                    self.tow = self.tow + seconds

                tow = self.tow - (self.tow + 1) % 2
                self.datetime  = time_now  

                svid, word_type, inav = parsed_sfrbx
                bit_array_inav = get_bit_array(list(inav))
                data_format    = DataFormat(svid, self.wn, tow, bit_array_inav)                    
                break
            
        if data_format is None:
            raise StopIteration
        
        return data_format 

class UBXLive(PageIterator):
    
    def __init__(self, host, port) -> None: 
        super().__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))
        self.tow_wn_dict = dict()
    
    def __next__(self) -> 'DataFormat': 
        
        data_format = None

        while sync := self.s.recv(2):

            if len(sync) < 2: 
                continue
    
            if (sync[0], sync[1]) != SYNC: 
                continue

            if  ( header := self.file.recv(4) ) == b'':  #no data 
                break

            class_id, length = parse_header(header)
            frame            = header + self.recv(length + 2) 
            is_valid_frame   = check_sum(frame)
        
            if is_valid_frame and class_id == UBX_RXM_SFRBX: 
                parsed_sfrbx = parse_sfrbx(self.tow_wn_dict, frame[4:-2])

                if parsed_sfrbx == "error":
                    continue

                svid, inav     = parsed_sfrbx
                tow,    wn     = self.tow_wn_dict[svid]
                bit_array_inav = get_bit_array(list(inav))
                data_format    = DataFormat(svid, wn, tow, bit_array_inav)
                break
            
            elif is_valid_frame and class_id == UBX_TIM_TP:               

                for svid in self.tow_wn_dict:
                    tow, wn                = self.tow_wn_dict[svid]
                    self.tow_wn_dict[svid] = (tow + 1, wn)
        
        if data_format is None:
            raise StopIteration
        
        return data_format
