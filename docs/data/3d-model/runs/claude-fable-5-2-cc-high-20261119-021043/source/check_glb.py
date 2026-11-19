import json, struct, sys
p = sys.argv[1]
b = open(p, 'rb').read()
magic, ver, length = struct.unpack('<III', b[:12])
clen, ctype = struct.unpack('<II', b[12:20])
j = json.loads(b[20:20 + clen])
print('size MB', round(len(b) / 1e6, 2), 'ext used', j.get('extensionsUsed'), 'required', j.get('extensionsRequired'))
print('nodes', [(n.get('name'), n.get('rotation'), n.get('translation')) for n in j['nodes'] if 'pivot' in n.get('name','')])
for m in j['meshes']:
    print('mesh', m['name'], 'prims', len(m['primitives']), 'targets', [len(pr.get('targets', [])) for pr in m['primitives']], 'weights', m.get('weights'), m.get('extras'))
for a in j.get('animations', []):
    print('anim', a.get('name'), 'channels', [(j['nodes'][c['target']['node']].get('name'), c['target']['path']) for c in a['channels']])
    for s in a['samplers']:
        acc = j['accessors'][s['input']]
        print('   sampler in count', acc['count'], 'min', acc.get('min'), 'max', acc.get('max'), s.get('interpolation'))
print('materials', [(m['name'], m.get('emissiveFactor'), m.get('extensions')) for m in j['materials']])
tri = 0
for m in j['meshes']:
    for pr in m['primitives']:
        tri += j['accessors'][pr['indices']]['count'] // 3
print('triangles', tri)
