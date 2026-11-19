import ctypes as C
import math
import random
import subprocess
import wave
from array import array
from functools import lru_cache
from pathlib import Path

WIDTH, HEIGHT, FPS, FRAMES = 1280, 720, 30, 294
ROOT = Path(__file__).resolve().parent
FRAMEWORKS = '/System/Library/Frameworks'
quartz = C.CDLL(f'{FRAMEWORKS}/CoreGraphics.framework/CoreGraphics')
textkit = C.CDLL(f'{FRAMEWORKS}/CoreText.framework/CoreText')
foundation = C.CDLL(f'{FRAMEWORKS}/CoreFoundation.framework/CoreFoundation')
P, D, U, I = C.c_void_p, C.c_double, C.c_uint32, C.c_size_t


class Point(C.Structure):
    _fields_ = [('x', D), ('y', D)]


class Rect(C.Structure):
    _fields_ = [('origin', Point), ('width', D), ('height', D)]

    def __init__(self, x, y, width, height):
        super().__init__(Point(x, y), width, height)


class Affine(C.Structure):
    _fields_ = [(name, D) for name in 'abcdef']


def bind(library, name, result, *args):
    function = getattr(library, name)
    function.restype = result
    function.argtypes = args
    return function


rgb_space = bind(quartz, 'CGColorSpaceCreateDeviceRGB', P)()
bitmap = bind(quartz, 'CGBitmapContextCreate', P, P, I, I, I, I, P, U)
rgba = bind(quartz, 'CGContextSetRGBFillColor', None, P, D, D, D, D)
stroke_rgba = bind(quartz, 'CGContextSetRGBStrokeColor', None, P, D, D, D, D)
begin = bind(quartz, 'CGContextBeginPath', None, P)
move = bind(quartz, 'CGContextMoveToPoint', None, P, D, D)
segment = bind(quartz, 'CGContextAddLineToPoint', None, P, D, D)
curve = bind(quartz, 'CGContextAddCurveToPoint', None, P, D, D, D, D, D, D)
close = bind(quartz, 'CGContextClosePath', None, P)
fill = bind(quartz, 'CGContextFillPath', None, P)
stroke = bind(quartz, 'CGContextStrokePath', None, P)
width_for_line = bind(quartz, 'CGContextSetLineWidth', None, P, D)
ellipse = bind(quartz, 'CGContextFillEllipseInRect', None, P, Rect)
save = bind(quartz, 'CGContextSaveGState', None, P)
restore = bind(quartz, 'CGContextRestoreGState', None, P)
clip_rect = bind(quartz, 'CGContextClipToRect', None, P, Rect)
translate = bind(quartz, 'CGContextTranslateCTM', None, P, D, D)
rotate = bind(quartz, 'CGContextRotateCTM', None, P, D)
set_alpha = bind(quartz, 'CGContextSetAlpha', None, P, D)
text_position = bind(quartz, 'CGContextSetTextPosition', None, P, D, D)
text_matrix = bind(quartz, 'CGContextSetTextMatrix', None, P, Affine)
new_color = bind(quartz, 'CGColorCreate', P, P, C.POINTER(D))
new_string = bind(foundation, 'CFStringCreateWithCString', P, P, C.c_char_p, U)
new_dict = bind(foundation, 'CFDictionaryCreate', P, P, C.POINTER(P), C.POINTER(P), C.c_long, P, P)
new_attributed = bind(foundation, 'CFAttributedStringCreate', P, P, P, P)
cf_release = bind(foundation, 'CFRelease', None, P)
new_font = bind(textkit, 'CTFontCreateWithName', P, P, D, P)
new_line = bind(textkit, 'CTLineCreateWithAttributedString', P, P)
draw_text = bind(textkit, 'CTLineDraw', None, P, P)
font_key = P.in_dll(textkit, 'kCTFontAttributeName').value
color_key = P.in_dll(textkit, 'kCTForegroundColorAttributeName').value

pixels = (C.c_ubyte * (WIDTH * HEIGHT * 4))()
ctx = bitmap(pixels, WIDTH, HEIGHT, 8, WIDTH * 4, rgb_space, 0x2006)
bind(quartz, 'CGContextSetLineCap', None, P, C.c_int)(ctx, 1)
bind(quartz, 'CGContextSetLineJoin', None, P, C.c_int)(ctx, 1)
text_matrix(ctx, Affine(1, 0, 0, 1, 0, 0))


@lru_cache(maxsize=None)
def color(swatch):
    return tuple(int(swatch[p:p+2], 16) / 255 for p in (0, 2, 4))


def ink(swatch, opacity=1):
    rgba(ctx, *color(swatch), opacity)


def polygon(points, swatch, opacity=1):
    ink(swatch, opacity)
    begin(ctx)
    move(ctx, *points[0])
    for position in points[1:]:
        segment(ctx, *position)
    close(ctx)
    fill(ctx)


def dot(position, radius, swatch, opacity=1):
    x, y = position
    ink(swatch, opacity)
    ellipse(ctx, Rect(x-radius, y-radius, radius*2, radius*2))


def line(points, swatch, thickness=1, opacity=1):
    stroke_rgba(ctx, *color(swatch), opacity)
    width_for_line(ctx, thickness)
    begin(ctx)
    move(ctx, *points[0])
    for position in points[1:]:
        segment(ctx, *position)
    stroke(ctx)


def path(commands, swatch, alpha=1, thickness=0):
    begin(ctx)
    move(ctx, *commands[0])
    for command in commands[1:]:
        if len(command) == 6:
            curve(ctx, *command)
        else:
            segment(ctx, *command)
    if thickness:
        stroke_rgba(ctx, *color(swatch), alpha)
        width_for_line(ctx, thickness)
        stroke(ctx)
    else:
        close(ctx)
        ink(swatch, alpha)
        fill(ctx)


@lru_cache(maxsize=None)
def typeset(string, font_name, size, swatch):
    string_ref = new_string(None, string.encode(), 0x08000100)
    name_ref = new_string(None, font_name.encode(), 0x08000100)
    font = new_font(name_ref, size, None)
    foreground = new_color(rgb_space, (D * 4)(*color(swatch), 1))
    attrs = new_dict(None, (P * 2)(font_key, color_key), (P * 2)(font, foreground), 2, None, None)
    attributed = new_attributed(None, string_ref, attrs)
    result = new_line(attributed)
    for ref in (attributed, attrs, foreground, font, name_ref, string_ref):
        cf_release(ref)
    return result


def lettering(string, font, size, swatch, x, y, progress=1, opacity=1):
    if progress <= 0 or opacity <= 0:
        return
    save(ctx)
    set_alpha(ctx, opacity)
    clip_rect(ctx, Rect(x-8, y-15, 760, size*progress+15))
    text_position(ctx, x, y - 18*(1-progress))
    draw_text(typeset(string, font, size, swatch), ctx)
    restore(ctx)


def ease(value):
    value = min(1, max(0, value))
    return value * value * (3 - 2 * value)


def beat(t, start, stop):
    return ease((t - start)/(stop - start))


def mix(a, b, p):
    return a+(b-a)*p


def paper():
    randomizer = random.Random(31054)
    grain = [round(randomizer.gauss(0, 1.4)) for _ in range(16384)]
    buffer = bytearray()
    for row in range(HEIGHT):
        y = 1 - row / HEIGHT
        for column in range(WIDTH):
            x = column / WIDTH
            halo = math.exp(-3.7*((x-0.51)**2+1.15*(y-0.47)**2))
            cloud = math.sin(x*20 + y*11)*math.sin(y*18-x*10) + math.cos(x*57+y*36)*0.33
            dust = grain[(row*3799+column) % len(grain)] + cloud*1.1
            buffer.extend((round(40 + 18*halo + dust), round(33 + 18*halo + dust),
                           round(16 + 13*halo + dust), 255))
    C.memmove(pixels, bytes(buffer), len(buffer))
    for _ in range(8800):
        x = randomizer.uniform(0, WIDTH)
        y = randomizer.uniform(0, HEIGHT)
        radius = randomizer.choice([0.48, 0.57, 0.7, 0.8, 1.15])
        dot((x,y), radius, randomizer.choice(('c2b694','07131c','839da1')), randomizer.uniform(0.05,0.24))
    return bytes(pixels)


SHEAR, DEPTH, RISE = 0.69, 0.49, 0.90


def paper_to_world(x, y):
    return (x+SHEAR*y/DEPTH, y/DEPTH)


def project(x, y, z):
    return (x-SHEAR*y, DEPTH*y+RISE*z)


class Tile:
    def __init__(self, x, y, dx, dy, palette, serial):
        self.x, self.y = paper_to_world(x, y)
        self.screen = x, y
        wx, wy = paper_to_world(dx, dy)
        self.yaw = math.atan2(wy, wx)
        self.palette = palette
        self.serial = serial
        rng = random.Random(1021+serial)
        self.height = rng.uniform(116, 118)
        self.half_width = rng.uniform(29, 30)
        self.half_depth = 8.5
        self.scuffs = [(rng.uniform(.08,.92), rng.uniform(.08,.92), rng.uniform(.5,2.85))
                       for _ in range(46)]

    def position(self, forward, lateral, height, pose):
        tilt, slide_x, slide_y, lift, turn = pose
        yaw = self.yaw + turn
        cos_yaw, sin_yaw = math.cos(yaw), math.sin(yaw)
        forward, height = (math.cos(tilt)*forward+math.sin(tilt)*height,
                           math.cos(tilt)*height-math.sin(tilt)*forward)
        wx, wy = paper_to_world(slide_x, slide_y)
        return (self.x+wx+cos_yaw*forward-sin_yaw*lateral,
                self.y+wy+sin_yaw*forward+cos_yaw*lateral, height+lift)

    def faces(self, pose):
        d, w, h, b = self.half_depth, self.half_width, self.height, 2.25
        f, r, s = self.palette
        vertices = [(d,-w+b), (d,w-b), (d-b,w), (-d+b,w), (-d,w-b), (-d,-w+b),
                    (-d+b,-w), (d-b,-w)]
        result = []
        swatches = (r, s, s, s, f, r, r, r)
        for index in range(8):
            start = vertices[index]
            end = vertices[(index+1) % 8]
            outline = [(*start,b), (*end,b), (*end,h-b), (*start,h-b)]
            result.append((outline, swatches[index], index))
            inset_start = (start[0]*.81, start[1]*.95)
            inset_end = (end[0]*.81, end[1]*.95)
            bevel = [(*start,h-b), (*end,h-b), (*inset_end,h), (*inset_start,h)]
            result.append((bevel, s, -1))
        result.append(([(x*.81,y*.95,h) for x,y in vertices], s, -1))
        for face, swatch, index in result:
            world = [self.position(*point, pose) for point in face]
            screen = [project(*point) for point in world]
            a, b, c = screen[:3]
            cross = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            if cross > 0:
                yield screen, swatch, index

    def shadow(self, pose):
        h, w, d = self.height, self.half_width, self.half_depth
        points = [self.position(f,l,z,pose) for f in (-d,d) for l in (-w,w) for z in (0,h)]
        shadow = hull([project(x+.55*z,y-.80*z,0) for x,y,z in points])
        for offset, opacity in ((6,.07),(3,.11),(0,.30)):
            polygon([(x+offset,y-offset) for x,y in shadow], '060e18', opacity)

    def draw(self, pose, paused=0):
        for screen, swatch, index in self.faces(pose):
            polygon(screen, swatch)
            if index in (0, 4):
                self.print_face(pose, index, paused)
            if index < 0:
                line(screen[:2], 'fff0d5', .65, .22)

    def print_face(self, pose, face, paused):
        d, w, h = self.half_depth, self.half_width, self.height
        sign = 1 if face == 0 else -1
        depth = d*sign
        printed = 'ffe5ba' if self.palette == HOT else '234858'

        def surface(u, v):
            return project(*self.position(depth, (u-.5)*(2*w-4)*sign, v*h, pose))

        for a, b, length in self.scuffs:
            finish = min(.97, b+length/h)
            line((surface(a,b),surface(a,finish)), '290f18', .6, .14)
        line((surface(.11,.13),surface(.89,.13)), printed, 1.15, .53)
        line((surface(.11,.87),surface(.89,.87)), printed, 1.15, .53)
        if paused < 1:
            arrow = [(0.19,.55),(.55,.55),(.55,.66),(.83,.50),(.55,.34),(.55,.45),(.19,.45)]
            polygon([surface(u,v) for u,v in arrow], printed, 1-paused)
        if paused:
            for left in (.28,.56):
                shape = [(left,.32),(left+.16,.32),(left+.16,.68),(left,.68)]
                polygon([surface(u,v) for u,v in shape], printed, paused)


def hull(points):
    def half(ordered):
        chain = []
        for c in ordered:
            while len(chain) > 1:
                a, b = chain[-2:]
                cross = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                if cross > 0:
                    break
                chain.pop()
            chain.append(c)
        return chain[:-1]
    ordered = sorted(points)
    return half(ordered)+half(reversed(ordered))


HOT = ('df512d','94352f','ff8656')
COOL = ('d3ccae','809e9d','f3e7c6')
MAIN = [(-33,102),(13,110),(61,121),(107,133),(152,147),(196,163),
        (239,180),(282,198),(325,216),(367,235),(410,253),(453,270),
        (497,285),(553,298),(621,305),(674,308),(726,308),(778,307),(830,306)]
BRANCHES = [
    [(813,332),(846,367),(883,401),(925,434),(972,462),(1023,487),(1078,509),
     (1134,528),(1193,543),(1252,554),(1314,561)],
    [(831,300),(883,307),(935,312),(987,315),(1039,317),(1091,316),(1143,312),
     (1196,305),(1249,295),(1304,281)],
    [(812,285),(846,250),(886,218),(931,190),(979,166),(1031,144),(1086,124),
     (1143,106),(1201,91),(1260,77),(1320,65)]
]
SELECTED = 13


def new_tiles(points, serial, outbreak=False):
    tiles = []
    for index, (x,y) in enumerate(points):
        prev = points[max(0,index-1)]
        nxt = points[min(index+1,len(points)-1)]
        palette = HOT if outbreak and index <= SELECTED else COOL
        tiles.append(Tile(x,y,nxt[0]-prev[0],nxt[1]-prev[1],palette,serial+index))
    return tiles


main = new_tiles(MAIN, 0, True)
branches = [tile for number, branch in enumerate(BRANCHES)
            for tile in new_tiles(branch[1:], 35+number*20)]


def fall_time(index):
    return 0.60 + index*.137 + .19*(1-math.exp(-.5*index))


def falling(t, index):
    if index >= SELECTED:
        return 0
    progress = max(0, (t-fall_time(index)))
    if not progress:
        return .12*beat(t, .12, .60) if index == 0 else 0
    tilt = 1.41*(1-math.exp(-11*progress))
    if index == SELECTED-1:
        tilt = mix(tilt,1.476,beat(progress,.2,.48))
    else:
        release = 2.73 + .028*(SELECTED-2-index)
        tilt = min(tilt, .97 + .4*beat(t, release, release+.23))
    return tilt


def intervention(t):
    grip = beat(t, 2.20, 2.42)
    remove = beat(t, 2.34, 2.83)
    settle = beat(t, 2.87, 3.70)
    pose = (-.25*remove+.14*settle, 38*remove+16*settle,
            -106*remove-51*settle, 33*remove+22*settle, .28*remove+.37*settle)
    return grip, remove, settle, pose

HAND = [(0,35), (-14,31,-19,45,-6,52), (6,60,18,51,31,40),
        (44,26,47,17,58,9), (69,14,77,9,81,1), (95,4,104,-7,105,-14),
        (121,-9,133,-22,139,-38), (155,-62,158,-81,191,-105),
        (212,-123),(170,-168),(146,-150), (121,-133,94,-126,78,-111),
        (56,-90,58,-60,36,-39), (27,-31,13,-24,7,-12),
        (-5,5,4,22,0,35)]
CLOTH = [(130,-132), (156,-125,185,-108,190,-92),
         (217,-107,271,-148,338,-191), (650,-448), (478,-615),
         (193,-241), (162,-193,148,-156,130,-132)]
THUMB = [(79,-92), (64,-81,54,-60,40,-44), (25,-36,2,-28,-7,-18),
         (-14,-10,-19,3,-12,10), (-3,17,13,7,22,0),
         (38,-11,48,-14,64,-23), (86,-34,94,-61,96,-79)]


def hand_layer(anchor, curl, foreground=False):
    save(ctx)
    translate(ctx, *anchor)
    rotate(ctx, -.06 + curl*.075)
    if foreground:
        path(THUMB, 'd58d72')
        path(THUMB[:5], '442630', .9, 1.55)
        path([(65,-24),(82,-33,87,-46,89,-60)], '6b3b43', .7, 1.3)
        path([(-10,4),(-4,9,4,5,11,-2),(8,-9,4,-11,-1,-13),(-9,-8,-12,-2,-10,4)], 'f0b49a')
        path([(-8,4),(-2,7,4,3,10,-2)], 'ffe4c3', .67, 1.1)
        path([(17,-13),(18,-17,17,-20,15,-23)], '773e47', .68, 1.05)
        path([(23,-16),(24,-19,24,-22,22,-25)], '773e47', .54, .85)
    else:
        save(ctx)
        translate(ctx, 27, -21)
        path(HAND, '0b1824', .46)
        path(CLOTH, '0b1824', .53)
        restore(ctx)
        path(HAND, 'bf775f')
        path(HAND, '653942', 1, 1.5)
        path([(0,35),(-9,35,-15,43,-7,49),(4,56,16,48,26,39),
              (41,24,49,19,58,9),(37,11,15,30,0,35)], 'eaa384')
        path([(36,-38),(52,-30,79,-28,98,-47),(113,-62,123,-87,151,-101),
              (134,-102,122,-99,114,-93),(95,-73,77,-81,55,-64)], 'd78a6d')
        path([(58,9),(68,0,68,-9,76,-20)], '77454b', .85, 1.65)
        path([(81,1),(90,-8,87,-13,93,-24)], '77454b', .85, 1.65)
        path([(105,-14),(109,-20,107,-26,114,-35)], '77454b', .85, 1.55)
        path([(126,-50),(132,-64,137,-73,146,-79)], '6d4049', .75, 1.05)
        for index in range(12):
            x, y = 116+2.05*index, -67-2.75*index
            line(((x,y),(x+8,y-7)), 'f4ac8c', .8, .46)
        path(CLOTH, '3d7580')
        path(CLOTH, '0a1f2e', 1, 2.25)
        path([(143,-149),(165,-145,188,-127,205,-106),
              (216,-113,225,-119,234,-126),(217,-152,193,-171,161,-177)], '255666')
        path([(134,-136),(156,-137,184,-111,195,-96)], 'bad0bd', .82, 2.25)
        path([(151,-165),(173,-161,202,-139,214,-114)], '80a7a5', .58, 1.3)
        path([(177,-187),(198,-180,229,-158,244,-138)], '9ab6b0', .5, 1.2)
        path([(186,-201),(216,-197,236,-175,249,-170),(278,-169,292,-188,326,-200)],
             '173d50', .8, 1.6)
        for index in range(18):
            x = 189+index*5
            y = -191-index*3.6
            line(((x,y),(x+11,y+4)), '86a9a7', .85, .26)
    restore(ctx)


def frame(t, background):
    C.memmove(pixels, background, len(background))
    grip, remove, settle, picked = intervention(t)
    target = main[SELECTED]
    show_hand = beat(t, 1.84, 2.35)
    rest = beat(t, 3.70, 4.95)
    breath = math.sin((t-3.7)*1.9)*1.4*rest
    picked = (picked[0]+breath*.009, picked[1], picked[2], picked[3]+breath, picked[4])
    hand_point = project(*target.position(0, -7, 31, picked))
    hand_point = (hand_point[0]+245*(1-show_hand)-8, hand_point[1]-352*(1-show_hand)-6)
    drawables = []
    still = (0,0,0,0,0)
    for tile in branches:
        drawables.append((tile.screen[1], tile, still, 0))
    for index, tile in enumerate(main):
        if index == SELECTED:
            if remove < .04:
                drawables.append((tile.screen[1], tile, picked, 0))
        else:
            tilt = falling(t,index)
            foot = tile.half_depth*math.sin(tilt)
            turn = .31*beat(t, 2.55, 2.98) if index == SELECTED-1 else 0
            drawables.append((tile.screen[1], tile, (tilt,0,0,foot,turn), 0))
    drawables.sort(key=lambda item: item[0], reverse=True)
    for _, tile, pose, _ in drawables:
        tile.shadow(pose)
    if remove >= .04:
        target.shadow(picked)
    draw_guide(t, remove)
    for _, tile, pose, paused in drawables:
        tile.draw(pose, paused)
    sparks(t)
    if show_hand:
        hand_layer(hand_point, grip)
    if remove >= .04:
        target.draw(picked, beat(t, 2.58, 3.15))
    if show_hand:
        hand_layer(hand_point, grip, True)
    opening = 1 - beat(t, 2.16, 2.62)
    face, italic = 'Georgia', 'Georgia-Italic'
    lettering('A rumor', face, 87, 'f5eacf', 74, 593, 1, opening)
    lettering('travels fast.', italic, 87, 'f7a27f', 71, 505, beat(t,-.19,.30), opening)
    lettering('Before you share,', face, 76, 'f5eacf', 74, 593, beat(t,3.45,4.22))
    lettering('check the source.', italic, 80, 'f7a27f', 71, 503, beat(t,3.84,4.62))
    return bytes(pixels)


def draw_guide(t, remove):
    # The marks on the table make the missing piece legible after the chain stops.
    for x,y in MAIN[1:-1]:
        line(((x-9,y-6),(x+10,y-1)), 'a8b5a4', .8, .22)
    x, y = main[SELECTED].screen
    if remove:
        line(((x-21,y-7),(x+14,y-9),(x+22,y+4),(x-13,y+6),(x-21,y-7)),
             'f2b48c', 1.4, remove*.63)
    ripple = (t-2.67)/.77
    if 0 < ripple < 1:
        for index in range(3):
            start = .21+index*.25
            radius = 13 + 51*ripple
            angle = start - .17*ripple
            ray = [(x+radius*math.cos(angle),y+radius*math.sin(angle)),
                   (x+(radius+10)*math.cos(angle),y+(radius+10)*math.sin(angle))]
            line(ray, 'fba177', 1.3, .4*math.sin(math.pi*ripple))


def sparks(t):
    for index, tile in enumerate(main[:SELECTED]):
        age = t - fall_time(index) - .07
        if not 0 < age < .42:
            continue
        x, y = tile.screen
        for number in range(6):
            angle = .69+number*.75+index*.38
            distance = (14+number*7)*age
            point = (x+38+distance*math.cos(angle), y+52+distance*math.sin(angle)+15*age)
            dot(point, .55+number*.14, 'faac77', (1-age/.42)*.68)


def audio(destination):
    rate = 32000
    points = int(rate*FRAMES/FPS)
    channels = [array('f', [0])*points for _ in range(2)]
    randomizer = random.Random(13)

    def event(start, duration, pan, sound):
        left, right = math.sqrt((1-pan)/2), math.sqrt((1+pan)/2)
        first = round(start*rate)
        for n in range(min(points-first,round(duration*rate))):
            value = sound(n/rate)
            channels[0][first+n] += left*value
            channels[1][first+n] += right*value

    tau = math.tau
    sine, exp = math.sin, math.exp
    for index in range(SELECTED):
        figure = (8-index%5)*8

        def clack(t):
            edge = min(1, t*3700)*exp(-93*t)
            wood = (sine(tau*t*(385+figure))*.60+sine(tau*t*(805+figure))*.26+
                    sine(tau*t*(1430+figure))*.14)
            return edge*(.25*wood+.12*randomizer.uniform(-1,1))

        tick = fall_time(index)+.071
        event(tick, .13, -.72+index*.058, clack)
        event(tick+.067, .10, -.47+index*.06, lambda t: clack(t)*.17)

    event(0, 3.17, -.15, lambda t: .043*beat(t,0,.7)*(1-beat(t,2.53,3.14)) *
          (sine(tau*55*t)+.45*sine(tau*(110*t+.25*sine(tau*.33*t)))))
    event(2.24,.51,.1,lambda t: .068*sine(math.pi*t/.51)**2 *
          (.7*randomizer.uniform(-1,1)+.3*sine(tau*(75*t+70*t*t))))
    event(2.95,.45,.13,lambda t: .20*min(1,t*460)*exp(-17*t)*
          (sine(tau*107*t)+.31*sine(tau*262*t)))
    for start, pitch, pan, gain in ((3.62,220,-.34,.095),(4.02,329.63,.21,.086),
                                     (4.23,392,.38,.075),(4.57,523.25,-.15,.062),
                                     (5.39,440,.16,.047),(6.64,329.63,.24,.040)):
        event(start,4.8,pan,lambda t: gain*beat(t,0,.025)*exp(-1.04*t)*
              (sine(tau*pitch*t)+.24*exp(-1.8*t)*sine(tau*pitch*2.002*t)+
               .16*exp(-4*t)*sine(tau*pitch*3.98*t)))
    samples = array('h')
    for index, (left, right) in enumerate(zip(*channels)):
        end = 1-beat(index/rate,9.36,9.8)
        samples.extend((round(left*end*32767), round(right*end*32767)))
    with wave.open(str(destination),'wb') as file:
        file.setparams((2,2,rate,0,'NONE','not compressed'))
        file.writeframes(samples.tobytes())


def encode(preview=False):
    background = paper()
    tmp = ROOT / '.render'
    tmp.mkdir(exist_ok=True)
    if preview:
        times = [0.73,1.73,2.38,2.66,3.16,4.48,6.0]
        for t in times:
            subprocess.run(['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pixel_format','bgra',
                            '-video_size',f'{WIDTH}x{HEIGHT}','-i','-','-frames:v','1','-vf','scale=896:504',
                            '-q:v','3',str(tmp/f'{t:04.2f}.jpg')], input=frame(t,background), check=True)
        return
    wavfile = tmp/'score.wav'
    audio(wavfile)
    command = ['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pixel_format','bgra',
               '-video_size',f'{WIDTH}x{HEIGHT}','-framerate',str(FPS),'-i','-','-i',str(wavfile),
               '-vf','scale=out_color_matrix=bt709,format=yuv420p','-c:v','libx264','-preset','slow',
               '-crf','18','-maxrate','1350k','-bufsize','800k','-af','volume=5dB','-c:a','aac','-b:a','96k',
               '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
               '-movflags','+faststart','-metadata','title=The Gap',str(ROOT/'output'/'the-gap.mp4')]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for number in range(FRAMES):
            encoder.stdin.write(frame(number/FPS, background))
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError('ffmpeg failed')
    wavfile.unlink()


if __name__ == '__main__':
    import sys
    encode('--preview' in sys.argv)
