import struct
import argparse
import re
from math import ceil
from subprocess import run, PIPE

encoding = "utf_16_le"
default_blocksize = 8192
dir_header_size = 2*4 + 2*2
main_header_size = 6*4
default_magic = 1145258838
default_version = 1

data_align = 512

def valve_crc32(data):
    p = run(['./crc32/valve_crc32'], stdout=PIPE, input=data)
    return int(p.stdout.decode("ascii").strip())


class DirEntry:
    
    def __init__(self, key=None, content=""):
        self.entry_hash = 0
        self.blocknum = 0
        self.offset = 0
        self.length = 0
        self.content = content
        if key is not None:
            self.entry_hash = valve_crc32(key.lower().encode("ascii"))
    
    def read_dir(self, fp):
        self.entry_hash, self.blocknum, self.offset, self.length = struct.unpack('IiHH', fp.read(dir_header_size))
        return self
    
    def write_dir(self, fp):
        fp.write(struct.pack("IiHH", self.entry_hash, self.blocknum, self.offset, self.length))

    def read_content(self, blocks):
        myblock = blocks[self.blocknum]
        mydata = myblock[self.offset : self.offset + self.length]
        self.content = mydata.decode(encoding)
        
    def write_content(self, blocks):
        mydata = self.content.encode(encoding) + b"\x00\x00"
        
        self.length = len(mydata)
        self.blocknum = len(blocks)-1
        myblock = blocks[self.blocknum]
        
        if self.length + len(myblock) > default_blocksize:
            for _ in range(default_blocksize - len(myblock)): blocks[self.blocknum] += b"\x00"
            blocks.append(b"")
            self.blocknum = len(blocks)-1
            myblock = blocks[self.blocknum]
            
        self.offset = len(myblock)
        blocks[self.blocknum] += mydata
        
    def describe(self):
        print("Block %08d (block %d, offset %d, length %d): \"%s\"" % (self.entry_hash, self.blocknum, self.offset, self.length, self.content))
        
    


def parsecli():
    parser = argparse.ArgumentParser(description="Read/write half life closed caption .dat files")
    parser.add_argument('-d', '--dir', help='print directory', action='store_true')
    parser.add_argument('-c', '--create', help='create from txt file', type=str)
    parser.add_argument('file', help='file containing the closed caption', type=str)

    return parser.parse_args()


def describe(cli, fp):
    entries = []
    blocks = []
    
    magic, version, numblocks, blocksize, directorysize, dataoffset = struct.unpack('iiiiii', fp.read(main_header_size))
    print("Magic: %d, Version: %d, Dir. size: %d\nNum. blocks: %d, Blocksize: %d, Dataoffset: %d" % (magic, version, directorysize, numblocks, blocksize, dataoffset))
    
    for d in range(directorysize):
        entries.append(DirEntry().read_dir(fp))
        
    fp.seek(dataoffset)
    
    for b in range(numblocks):
        blocks.append(fp.read(blocksize))
        
    for entry in entries:
        entry.read_content(blocks)
        
    entries = sorted(entries, key=lambda e: e.entry_hash)
    
    if cli.dir:
        for entry in entries:
            entry.describe()
            
            
def write(cli, fp_write):
    blocks = [b""]
    entries = []
    
    with open(cli.create, "r", encoding=encoding) as fp_read:
        lines = fp_read.read().split("\n")
        for line in lines:
            linematch = re.compile("\"([^\"]+)\"\s+\"([^\"]+)\"").match(line)
            if linematch is None:
                continue
            
            key = linematch.group(1)
            sentence = linematch.group(2)
            if key == "Language": continue
            if key.startswith("[english]"): continue
        
            entry = DirEntry(key, sentence)
            entry.write_content(blocks)
            entries.append(entry)
    
    lastblock = blocks[len(blocks) - 1]
    for _ in range(default_blocksize - len(lastblock)): lastblock += b"\x00"
            
            
    raw_dataoffset = main_header_size + len(entries) * dir_header_size
    dataoffset = int(ceil(raw_dataoffset / data_align) * data_align)
    
    fp_write.write(struct.pack('iiiiii', default_magic, default_version, len(blocks), default_blocksize, len(entries), dataoffset))
    
    for entry in entries:
        entry.write_dir(fp_write)
        
    curs_pos = fp_write.tell()
    for _ in range(dataoffset - curs_pos): fp_write.write(b"\x00")
    
    for block in blocks:
        fp_write.write(block)
        
    curs_pos = fp_write.tell()
    padded_size = int(ceil(curs_pos / data_align) * data_align)
    for _ in range(padded_size - curs_pos): fp_write.write(b"\x00")

def main(cli):
    if cli.create:
        with open(cli.file, "wb") as fp:
            write(cli, fp)
    else:
        with open(cli.file, "rb") as fp:
            describe(cli, fp)


if __name__ == "__main__":
    cli = parsecli()
    main(cli)
