import reedsolo

info_v_file = 'rs_information_vector_example.csv'
code_v_file = 'rs_code_vector_example.csv'

with open(info_v_file, 'r') as f:
    info_v_str = f.read().strip().split(';')
    info_v = bytearray([int(v) for v in info_v_str])

with open(code_v_file, 'r') as f:
    code_v_str = f.read().strip().split(';')
    code_v = bytearray([int(v) for v in code_v_str])

print(info_v)

n = 255                     # Total codeword length (n)
k = 195                     # Information vector length (k)
parity_symbols = n - k      # Parity symbols = 60
rs = reedsolo.RSCodec(parity_symbols, nsize=n, fcr=1, prim=0x11d)  # x^8 + x^4 + x^3 + x^2 + 1

encoded_v = rs.encode(info_v[::-1])
encoded_v_fixed = encoded_v[:58][::-1] + encoded_v[58:][::-1]

print(encoded_v_fixed)
print(code_v)

