"""Strict non-interlaced 8-bit RGB(A) PNG verification and full pixel decode."""
from pathlib import Path
import struct, zlib, hashlib
def decode_png(path, expected=(1280,720)):
    data=Path(path).read_bytes()
    assert data[:8]==b'\x89PNG\r\n\x1a\n'
    pos=8; compressed=bytearray(); chunks=[]; header=None
    while pos<len(data):
        size=struct.unpack_from('>I',data,pos)[0]
        kind=data[pos+4:pos+8]; block=data[pos+8:pos+8+size]
        assert len(block)==size and pos+12+size<=len(data)
        crc=struct.unpack_from('>I',data,pos+8+size)[0]
        assert zlib.crc32(kind+block)&0xffffffff==crc, 'PNG CRC mismatch'
        chunks.append(kind.decode('ascii')); pos+=12+size
        if kind==b'IHDR': header=struct.unpack('>IIBBBBB',block)
        if kind==b'IDAT': compressed.extend(block)
        if kind==b'IEND': assert size==0 and pos==len(data); break
    assert chunks[0]=='IHDR' and chunks[-1]=='IEND'
    w,h,depth,color,comp,filt,interlace=header
    assert (w,h)==expected and depth==8 and color in (2,6) and not (comp or filt or interlace), header
    bpp=3 if color==2 else 4; stride=w*bpp
    dz=zlib.decompressobj(); raw=dz.decompress(compressed)+dz.flush()
    assert dz.eof and not dz.unused_data and len(raw)==h*(stride+1)
    pixels=bytearray(); prev=bytearray(stride)
    for y in range(h):
        off=y*(stride+1); mode=raw[off]; row=bytearray(raw[off+1:off+1+stride]); assert mode<=4
        if mode:
            for x in range(stride):
                a=row[x-bpp] if x>=bpp else 0; b=prev[x]; c=prev[x-bpp] if x>=bpp else 0
                if mode==1: v=a
                elif mode==2: v=b
                elif mode==3: v=(a+b)//2
                else:
                    p=a+b-c; pa,pb,pc=abs(p-a),abs(p-b),abs(p-c)
                    v=a if pa<=pb and pa<=pc else b if pb<=pc else c
                row[x]=(row[x]+v)&255
        pixels.extend(row); prev=row
    return {'width':w,'height':h,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'all_chunk_crcs_valid':True,'full_pixel_decode':True,'range':[min(pixels),max(pixels)],'chunks':chunks}
