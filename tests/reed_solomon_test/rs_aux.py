from bitstring import BitArray

word_1 = BitArray(hex='0468384300f9d51000283cd2a8134a1f')
word_2 = BitArray(hex='08680900a19727244c7f94321021f501')
word_3 = BitArray(hex='0c68ffc01025a3f3ff0e4c1852f0776b')
word_4 = BitArray(hex='106814007c000ce1009a5d85a000fe01')

word_17 = BitArray(hex='46c882c3d91575048e05eb3a0e8a3eb5')
word_18 = BitArray(hex='4b4c2daedfd30517ef41a79b281f5e4a')
word_19 = BitArray(hex='4f6ceb3cc7334fb27753ce6b5974e501')
word_20 = BitArray(hex='518c37d37a45f64e1767deff5de81321')


def create_info_vector(words=[None, None, None, None]) -> BitArray:
    info_vector = BitArray(58*8)
    if words[0] is not None:
        info_vector[0:128] = words[0]
        info_vector[6:8] = words[0][14:16]
        info_vector[8:16] = words[0][6:14]
    for i, word in enumerate(words[1:]):
        if word is not None:
            info_vector[128 + 112*i:128 + 112*(i+1)] = word[16:128]
    return info_vector

def create_parity_vector(words=[None, None, None, None]) -> BitArray:
    parity_vector = BitArray(60*8)
    for i, word in enumerate(words):
        if word is not None:
            parity_vector[120*i:(120*i)+8] = word[6:14]
            parity_vector[(120*i)+8:120*(i+1)] = word[16:128]
    return parity_vector

def swap_format(code_vector: bytearray) -> bytearray:
    """
    The information vector is 58 bytes, and the parity vector is 60 bytes.
    Each vector is reversed independently
    """
    reversed_vector = code_vector[:58][::-1] + code_vector[58:][::-1]
    return reversed_vector

def swap_erasure(erasures: list) -> list:
    fixed_erasures = [57-i if i <= 57 else 117-i+58 for i in erasures]
    return fixed_erasures


if __name__ == '__main__':
    print(word_1[6:16])
    print(word_2[6:16])
    print(word_3[6:16])
    print(word_4[6:16])
    print(word_17[14:16])
    print(word_18[14:16])
    print(word_19[14:16])
    print(word_20[14:16])
    word_1[6:16] = BitArray(bin='1010101001')
    print(word_1[6:16])
    print(word_1[6:16][-2:])

