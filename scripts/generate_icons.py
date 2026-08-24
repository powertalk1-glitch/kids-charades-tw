"""以純 Python 產生比手畫腳 PWA 圖示。"""
from pathlib import Path
import struct, zlib
ROOT=Path(__file__).resolve().parents[1]/'icons'
ROOT.mkdir(exist_ok=True)

def png(path,size):
    navy=(23,50,77); cream=(255,248,232); coral=(242,107,94); mint=(120,214,181); yellow=(255,209,102)
    rows=[]
    for y in range(size):
        row=bytearray([0])
        for x in range(size):
            nx=(x-size/2)/(size/2); ny=(y-size/2)/(size/2); r2=nx*nx+ny*ny
            color=navy
            if r2<.67: color=cream
            # two playful theatre faces, composed from flat circles
            left=((x-size*.39)/(size*.22))**2+((y-size*.50)/(size*.25))**2<1
            right=((x-size*.61)/(size*.22))**2+((y-size*.50)/(size*.25))**2<1
            if left: color=coral
            if right: color=mint
            # eyes
            eye=((x-size*.33)/(size*.025))**2+((y-size*.45)/(size*.035))**2<1 or ((x-size*.45)/(size*.025))**2+((y-size*.45)/(size*.035))**2<1 or ((x-size*.55)/(size*.025))**2+((y-size*.45)/(size*.035))**2<1 or ((x-size*.67)/(size*.025))**2+((y-size*.45)/(size*.035))**2<1
            if eye: color=navy
            # happy mouths and confetti
            mouth_left=((x-size*.39)/(size*.105))**2+((y-size*.57)/(size*.065))**2<1 and y>size*.57
            mouth_right=((x-size*.61)/(size*.105))**2+((y-size*.57)/(size*.065))**2<1 and y>size*.57
            if mouth_left or mouth_right: color=navy
            if ((x-size*.26)**2+(y-size*.24)**2 < (size*.025)**2) or ((x-size*.74)**2+(y-size*.28)**2 < (size*.025)**2): color=yellow
            row.extend((*color,255))
        rows.append(bytes(row))
    raw=b''.join(rows)
    def chunk(kind,data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    payload=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
    path.write_bytes(payload)
for name,size in [('icon-192.png',192),('icon-512.png',512),('apple-touch-icon.png',180)]: png(ROOT/name,size)
print('已產生 192、512 與 Apple 180 PNG 圖示')
