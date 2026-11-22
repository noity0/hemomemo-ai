"""
🔐 security/hmhz.py — HMHZ SECRET LANGUAGE (apni coding-language + VM)

User qanoon: "ek aisi coding language banao jo secret ho, jise kholna bohat
mushkil ho, koi nahi janta — koi break nahi kar sake. Security ki 5 layers:
4 normal tech se + 1 HMHZ se."

HMHZ KYA HAI (100% asli, 100% local — koi API/AI/internet nahi):
  1. APNI LANGUAGE  : chhota stack-VM assembly (16 opcodes) jo SIRF is file
     ka interpreter samajhta hai. Duniya me iska koi parser/compiler nahi.
  2. APNA ENCODING  : bytecode par (a) rolling-XOR key "HMHZ-SEC" + position,
     (b) nibble-swap odd bytes, (c) APNA base32 alphabet — teeno layers ke
     baghair bytes kisi standard tool me decode NAHI hote (magic bhi custom:
     file "HMHZ1" se shuru hoti hai).
  3. INTEGRITY      : bytecode me CRC32 embedded hai — ek bit badla → foran
     REFUSE (tamper-proof policy).
  4. HONEST SCOPE   : ye jaan-boojh kar banayi gayi OBSCURITY+INTEGRITY layer
     hai (security-through-custom-VM) — iske aage integrity L3 (sha256) aur
     network L1 (net_guard) khare hain. HMHZ akela kaafi nahi — 5-layer stack
     ka hissa hai.

ASSEMBLY (HMHZ-asm):
    PUSH <int|"string">     stack par value
    POP                     top nikaal
    ADD / SUB / MUL         top 2 numbers
    CMP                     top 2 barabar? → 1/0
    LOAD <cell> / STORE <cell>     memory cells (0..63)
    IN <name>               ctx se value push (misal: IN prompt)
    MATCH                   stack: [pattern, text] → text me pattern? 1/0
    LEN                     top string ki lambai
    JMP <label> / JZ <label>       control-flow
    OUT                     top ko result me daal (vm.out list)
    HALT                    ruk jao

FILE FORMAT (.hmhz — text):
    HMHZ1
    <custom-base32 lines>

CLI:
    py -3 security/hmhz.py compile security/policy.hmhzsrc security/policy.hmhz
    py -3 security/hmhz.py run security/policy.hmhz --in prompt="kuch likha"
"""
import base64
import binascii
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(HERE)
else:
    ROOT = os.path.dirname(HERE)

MAGIC = "HMHZ1"
KEY = b"HMHZ-SEC"                      # rolling-XOR key (custom)
ALPHABET = "HMZKAJ9XVQTW5NPR7Y2DLBC8E6F4GS3U"   # HMHZ apna base32 (custom)

# ----------------------------------------------------------------- opcodes
OP = {"NOP": 0x00, "PUSH": 0x01, "POP": 0x02, "ADD": 0x03, "SUB": 0x04,
      "MUL": 0x05, "CMP": 0x06, "JMP": 0x07, "JZ": 0x08, "LOAD": 0x09,
      "STORE": 0x0A, "IN": 0x0B, "MATCH": 0x0C, "LEN": 0x0D, "INSTR": 0x0E,
      "OUT": 0x0F, "HALT": 0x10}
OPNAME = {v: k for k, v in OP.items()}
MAX_CELL = 64

# ----------------------------------------------------------------- compile
_TOK = re.compile(r'"[^"]*"|\S+')


def compile_src(src: str) -> bytes:
    """HMHZ-asm → raw bytecode (labels BYTE-offsets par resolve — 🛠️ fix:
    pehle labels instruction-index bante the magar VM ka pc BYTE-offset par
    jump karta hai → JZ-taken path beech bytecode me girta tha). Offsets JZ
    arg ki lambai par munhasir hain → fixpoint tak dohrao."""
    lines, label_at, jumps = [], {}, {}
    for ln in src.splitlines():
        ln = ln.split("#", 1)[0].strip()
        if not ln:
            continue
        if ln.endswith(":"):
            label_at[ln[:-1].strip()] = len(lines)
            continue
        lines.append(ln)
    for idx, ln in enumerate(lines):
        toks = _TOK.findall(ln)
        if toks and toks[0].upper() in ("JMP", "JZ") and len(toks) > 1:
            jumps[idx] = toks[1]

    def _size(idx, jarg_len):
        toks = _TOK.findall(lines[idx])
        op = toks[0].upper()
        n = 2                                  # opcode + 0x1F separator
        if op in ("PUSH", "LOAD", "STORE", "IN"):
            n += len(toks[1]) if len(toks) > 1 else 0
        elif op in ("JMP", "JZ"):
            n += jarg_len
        return n

    labels = {}
    for _round in range(8):
        offs, t = [], 0
        for idx in range(len(lines)):
            offs.append(t)
            jl = len(str(labels.get(jumps[idx], 0))) if idx in jumps else 0
            t += _size(idx, jl)
        new_labels = {nm: offs[i] for nm, i in label_at.items()}
        if new_labels == labels:
            break
        labels = new_labels
    code = bytearray()
    for ln in lines:
        toks = _TOK.findall(ln)
        op = toks[0].upper()
        if op not in OP:
            raise ValueError("HMHZ-compile: anjaan opcode %r" % toks[0])
        code.append(OP[op])
        arg = toks[1] if len(toks) > 1 else None
        if op in ("JMP", "JZ"):
            if arg is None or arg not in labels:
                raise ValueError("HMHZ-compile: label %r nahi mila" % arg)
            code += str(labels[arg]).encode()
        elif op in ("PUSH", "LOAD", "STORE", "IN"):
            if arg is None:
                raise ValueError("HMHZ-compile: %s ko arg chahiye" % op)
            if arg.startswith('"'):
                code += b'"' + arg[1:-1].encode("utf-8") + b'"'
            else:
                code += arg.encode()
        code.append(0x1F)                     # instruction-separator (apna)
    return bytes(code)


# ----------------------------------------------------------------- encoding
def _xor_roll(data: bytes) -> bytes:
    out = bytearray()
    for i, b in enumerate(data):
        out.append(b ^ KEY[i % len(KEY)] ^ (i & 0xFF))
    return bytes(out)


def _nibbleswap(data: bytes) -> bytes:
    out = bytearray()
    for i, b in enumerate(data):
        out.append(((b << 4) | (b >> 4)) & 0xFF if i % 2 else b)
    return bytes(out)


def encode(raw: bytes) -> str:
    """bytecode → HMHZ1 text-file content (3-layer custom encoding)."""
    raw = raw + zlib.crc32(raw).to_bytes(4, "big")   # integrity seal
    x = _xor_roll(raw)
    x = _nibbleswap(x)
    b32 = base64.b32encode(x).decode()               # standard b32 pehle
    # standard alphabet → HMHZ apna alphabet (koi standard tool nahi pehchanta)
    table = {}
    std = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    for a, h in zip(std, ALPHABET):
        table[a] = h
    mapped = "".join(table.get(c, c) for c in b32.rstrip("="))
    lines = [MAGIC]
    for i in range(0, len(mapped), 40):
        lines.append(mapped[i:i + 40])
    return "\n".join(lines) + "\n"


def decode(text: str) -> bytes:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines or lines[0] != MAGIC:
        raise ValueError("HMHZ: magic nahi — ye HMHZ file nahi")
    mapped = "".join(lines[1:])
    rev = {h: a for a, h in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567", ALPHABET)}
    std = "".join(rev.get(c, c) for c in mapped)
    pad = "=" * ((8 - len(std) % 8) % 8)
    x = base64.b32decode(std + pad)
    x = _nibbleswap(x)
    raw = _xor_roll(x)
    body, seal = raw[:-4], raw[-4:]
    if zlib.crc32(body).to_bytes(4, "big") != seal:
        raise ValueError("HMHZ: INTEGRITY-FAIL — bytecode tamper/shayad badla")
    return body


# ----------------------------------------------------------------- VM
class VM:
    """HMHZ stack-VM — sirf isi file ka interpreter is bytecode ko chala sakta."""

    def __init__(self, code: bytes, ctx: dict = None):
        self.code = code
        self.ctx = ctx or {}
        self.stack = []
        self.cells = [None] * MAX_CELL
        self.out = []
        self.pc = 0

    def _read_arg(self):
        end = self.code.index(0x1F, self.pc)
        arg = self.code[self.pc:end]
        self.pc = end + 1
        if arg.startswith(b'"'):
            return arg[1:-1].decode("utf-8", "replace")
        s = arg.decode("ascii", "replace")
        try:
            return int(s)
        except ValueError:
            return s

    def run(self, max_steps: int = 20000) -> list:
        steps = 0
        while self.pc < len(self.code):
            steps += 1
            if steps > max_steps:
                raise RuntimeError("HMHZ-VM: step-limit (loop shayad band hai)")
            if self.code[self.pc] == 0x1F:      # instruction-separator skip
                self.pc += 1
                continue
            op = self.code[self.pc]
            self.pc += 1
            if op == OP["NOP"]:
                pass
            elif op == OP["PUSH"]:
                self.stack.append(self._read_arg())
            elif op == OP["POP"]:
                self.stack.pop()
            elif op == OP["ADD"]:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)
            elif op == OP["SUB"]:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)
            elif op == OP["MUL"]:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a * b)
            elif op == OP["CMP"]:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(1 if a == b else 0)
            elif op == OP["JMP"]:
                self.pc = int(self._read_arg())
            elif op == OP["JZ"]:
                tgt = int(self._read_arg())
                if not self.stack.pop():
                    self.pc = tgt
            elif op == OP["LOAD"]:
                self.stack.append(self.cells[int(self._read_arg()) % MAX_CELL])
            elif op == OP["STORE"]:
                c = int(self._read_arg())
                self.cells[c % MAX_CELL] = self.stack.pop()
            elif op == OP["IN"]:
                self.stack.append(self.ctx.get(str(self._read_arg()), ""))
            elif op == OP["MATCH"]:
                txt = str(self.stack.pop())
                pat = str(self.stack.pop())
                self.stack.append(1 if pat.lower() in txt.lower() else 0)
            elif op == OP["LEN"]:
                self.stack.append(len(str(self.stack.pop())))
            elif op == OP["INSTR"]:            # substring: [start,text] → text[start:start+n]
                n = int(self.stack.pop())
                txt = str(self.stack.pop())
                self.stack.append(txt[:n])
            elif op == OP["OUT"]:
                self.out.append(self.stack.pop())
            elif op == OP["HALT"]:
                break
            else:
                raise ValueError("HMHZ-VM: anjaan opcode 0x%02x" % op)
        return self.out


# ----------------------------------------------------------------- file I/O
def compile_file(src_path: str, out_path: str) -> str:
    with open(src_path, encoding="utf-8") as f:
        text = encode(compile_src(f.read()))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return out_path


def run_file(path: str, ctx: dict = None) -> list:
    with open(path, encoding="utf-8") as f:
        return VM(decode(f.read()), ctx).run()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) >= 4 and sys.argv[1] == "compile":
        out = compile_file(sys.argv[2], sys.argv[3])
        print("HMHZ-COMPILE-OK →", out, os.path.getsize(out), "bytes")
    elif len(sys.argv) >= 3 and sys.argv[1] == "run":
        ctx = {}
        for kv in sys.argv[3:]:
            k, _, v = kv.partition("=")
            ctx[k] = v
        print("HMHZ-OUT:", run_file(sys.argv[2], ctx))
    else:
        print("istemaal: py -3 security/hmhz.py compile <src> <out> | run <file> --in k=v")
