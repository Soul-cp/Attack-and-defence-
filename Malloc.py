from pwn import *
from keystone import *

# 1. Define the assembly you want to inject
# Example: We want to replace a vulnerable instruction with a safe one
asm_code = "mov eax, 1; ret" 

# 2. Assemble it to raw bytes
ks = Ks(KS_ARCH_X86, KS_MODE_64)
encoding, count = ks.asm(asm_code)
patch_bytes = bytes(encoding)

# 3. Open the binary and write the bytes at the specific offset
with open("vulnerable_binary", "r+b") as f:
    f.seek(0x1234) # The file offset you found in Ghidra/Rizin
    f.write(patch_bytes)
    
print("Binary Patched!")