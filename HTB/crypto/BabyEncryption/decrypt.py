import binascii

with open("msg.enc", "r") as f:
    cipher = binascii.unhexlify(f.read())

decrypted_msg = "".join([chr((b-18) * pow(123, -1, 256) % 256) for b in cipher])

print(decrypted_msg)
