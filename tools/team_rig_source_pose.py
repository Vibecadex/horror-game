"""Independent stdlib evaluator for the team's translation/rotation glTF fixture."""
import bisect
import json
import math
from pathlib import Path
import struct


def multiply(a, b):
    x, y, z, w = a
    i, j, k, r = b
    return (w*i+x*r+y*k-z*j, w*j-x*k+y*r+z*i,
            w*k+x*j-y*i+z*r, w*r-x*i-y*j-z*k)


def rotate(q, v):
    return multiply(multiply(q, (*v, 0)), (-q[0], -q[1], -q[2], q[3]))[:3]


def slerp(a, b, t):
    dot = sum(x*y for x, y in zip(a, b))
    if dot < 0:
        b, dot = tuple(-x for x in b), -dot
    if dot > 0.9995:
        q = tuple(x + t*(y-x) for x, y in zip(a, b))
        length = math.sqrt(sum(x*x for x in q))
        return tuple(x/length for x in q)
    theta = math.acos(min(1, dot))
    sa, sb = math.sin((1-t)*theta)/math.sin(theta), math.sin(t*theta)/math.sin(theta)
    return tuple(sa*x+sb*y for x, y in zip(a, b))


class SourcePose:
    def __init__(self, path):
        raw = Path(path).read_bytes()
        magic, version, total = struct.unpack_from('<4sII', raw)
        assert magic == b'glTF' and version == 2 and total == len(raw)
        n, kind = struct.unpack_from('<I4s', raw, 12)
        assert kind == b'JSON'
        self.doc = json.loads(raw[20:20+n])
        m, kind = struct.unpack_from('<I4s', raw, 20+n)
        assert kind == b'BIN\0'
        self.blob = raw[28+n:28+n+m]
        self.parents = {child: i for i, node in enumerate(self.doc['nodes']) for child in node.get('children', [])}

    def accessor(self, index):
        a = self.doc['accessors'][index]
        v = self.doc['bufferViews'][a['bufferView']]
        assert a['componentType'] == 5126 and 'sparse' not in a
        width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
        stride = v.get('byteStride', width*4)
        offset = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        return [struct.unpack_from('<' + 'f'*width, self.blob, offset+i*stride) for i in range(a['count'])]

    def positions(self, clip=None, time=0):
        rotations = {}
        if clip:
            anim = next(a for a in self.doc['animations'] if a['name'] == clip)
            for ch in anim['channels']:
                assert ch['target']['path'] == 'rotation'
                sampler = anim['samplers'][ch['sampler']]
                assert sampler.get('interpolation', 'LINEAR') == 'LINEAR'
                times = [t[0] for t in self.accessor(sampler['input'])]
                values = self.accessor(sampler['output'])
                high = min(len(times)-1, max(1, bisect.bisect_left(times, time)))
                fraction = max(0, min(1, (time-times[high-1])/(times[high]-times[high-1])))
                rotations[ch['target']['node']] = slerp(values[high-1], values[high], fraction)
        global_ = {}

        def transform(i):
            if i in global_:
                return global_[i]
            node = self.doc['nodes'][i]
            assert 'matrix' not in node and node.get('scale', [1, 1, 1]) == [1, 1, 1]
            p = tuple(node.get('translation', [0, 0, 0]))
            q = rotations.get(i, tuple(node.get('rotation', [0, 0, 0, 1])))
            if i in self.parents:
                pp, pq = transform(self.parents[i])
                p = tuple(a+b for a, b in zip(pp, rotate(pq, p)))
                q = multiply(pq, q)
            global_[i] = p, q
            return p, q

        # Installed Interchange GLTF conversion: metres -> cm, (x,y,z) -> (x,z,y).
        return {self.doc['nodes'][i]['name']: [p[0]*100, p[2]*100, p[1]*100]
                for i in self.doc['skins'][0]['joints'] for p, _ in [transform(i)]}
