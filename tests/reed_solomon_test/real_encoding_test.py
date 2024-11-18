import reedsolo

from rs_aux import *

# Define Galileo RS(255, 195) parameters
n = 255             # Total codeword length (n)
k = 195             # Information vector length (k)
parity_symbols = n - k  # Parity symbols = 60

# Primitive polynomial for GF(256): x^8 + x^4 + x^3 + x^2 + 1
rs = reedsolo.RSCodec(60, nsize=n, fcr=1, prim=0x11d)

info_v_good = create_info_vector([word_1, word_2, word_3, word_4]).bytes
parity_v_good = create_parity_vector([word_17, word_18, word_19, word_20]).bytes
galileo_encoded = bytearray(info_v_good + parity_v_good)

library_encoded = rs.encode(info_v_good[::-1])
library_encoded_gal_format = swap_format(library_encoded)

print(f"info_v: {len(info_v_good)}")
print(f"parity_v: {len(parity_v_good)}")
print(f"Galileo encoded: n={len(galileo_encoded)}")
print(f"Library encoded: n={len(library_encoded_gal_format)}")

print(f"Galileo encoded:\n{galileo_encoded}")
print(f"Library encoded:\n{library_encoded_gal_format}")


# Corrupt message
galileo_with_erasures = bytearray(galileo_encoded)

erasures = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43]
erasures = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57]
erasures = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57]
erasures = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57]

erasures = [58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
erasures = [58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87]
erasures = [58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102]
erasures = [58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117]

# Erasing 2 from CED, 1 from ReedCED
erasures = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
# Erasing 2 from CED, 2 from ReedCED
erasures = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117]
# Erasing 2 form CED, 2 from ReedCED, but the 16 bytes one form CED
erasures = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87]
# Erasin 1 from CED and 3 from ReedCED. The first byte is known, else would be 61 erasures
erasures = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117]

for index in erasures:
    galileo_with_erasures[index] = 0

galileo_with_erasures_lib_format = swap_format(galileo_with_erasures)
decoded_msg, decoded_msgecc, errata_pos = rs.decode(galileo_with_erasures_lib_format, erase_pos=swap_erasure(erasures))
decoded_msgecc_gal_format = swap_format(decoded_msgecc)

print(f"Library corrected:\n{decoded_msgecc_gal_format}")
print(swap_erasure(list(errata_pos)))

if galileo_encoded == library_encoded_gal_format == decoded_msgecc_gal_format:
    print("ALL GOOD")
else:
    print("RIP")


