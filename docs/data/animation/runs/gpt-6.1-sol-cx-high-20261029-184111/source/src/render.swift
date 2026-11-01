import Foundation
import CoreGraphics
import CoreText

let W = 1080, H = 1080, fps = 30, frames = 300
struct Col {
    var r: CGFloat; var g: CGFloat; var b: CGFloat
    init(_ hex: UInt32) { r = CGFloat((hex >> 16) & 255)/255; g = CGFloat((hex >> 8) & 255)/255; b = CGFloat(hex & 255)/255 }
    func cg(_ a: CGFloat = 1) -> CGColor { CGColor(red:r,green:g,blue:b,alpha:a) }
}
let paper = Col(0xF5F0E5), ink = Col(0x25374B), muted = Col(0x6D7879), gold = Col(0xF2B94E)
let coral = Col(0xD96B50), teal = Col(0x3B817C), blue = Col(0x657EA0), rust = Col(0xA7513C), lilac = Col(0x9987A8)
func mix(_ a: Col, _ b: Col, _ q: Double) -> Col { let t = CGFloat(q); var c = a; c.r += (b.r-a.r)*t; c.g += (b.g-a.g)*t; c.b += (b.b-a.b)*t; return c }
func ease(_ a: Double, _ b: Double, _ t: Double) -> Double { let x = max(0,min(1,(t-a)/(b-a))); return x*x*(3-2*x) }
func lerp(_ a: Double, _ b: Double, _ t: Double) -> Double { a + (b-a)*t }
func p(_ x: Double,_ y: Double)->CGPoint { CGPoint(x:x,y:y) }
let bytes = W*H*4
let buffer = UnsafeMutableRawPointer.allocate(byteCount:bytes,alignment:64)
let ctx = CGContext(data:buffer,width:W,height:H,bitsPerComponent:8,bytesPerRow:W*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
ctx.translateBy(x:0,y:CGFloat(H)); ctx.scaleBy(x:1,y:-1)
func line(_ pts: [CGPoint], _ color: Col, _ width: Double, _ alpha: Double = 1) {
    guard let start = pts.first else { return }; ctx.beginPath();ctx.move(to:start)
    for pt in pts.dropFirst() { ctx.addLine(to:pt) }
    ctx.setStrokeColor(color.cg(CGFloat(alpha)));ctx.setLineWidth(width);ctx.setLineCap(.round);ctx.setLineJoin(.round);ctx.strokePath()
}
func curve(_ a: CGPoint, _ b: CGPoint, _ c: CGPoint, _ d: CGPoint, _ color:Col, _ width:Double, _ alpha:Double=1) {
    ctx.beginPath();ctx.move(to:a);ctx.addCurve(to:d,control1:b,control2:c);ctx.setStrokeColor(color.cg(CGFloat(alpha)));ctx.setLineWidth(width);ctx.setLineCap(.round);ctx.strokePath()
}
func ellipse(_ x:Double,_ y:Double,_ rx:Double,_ ry:Double,_ color:Col,_ alpha:Double=1) {ctx.setFillColor(color.cg(CGFloat(alpha)));ctx.fillEllipse(in:CGRect(x:x-rx,y:y-ry,width:rx*2,height:ry*2))}
func polygon(_ points:[CGPoint],_ color:Col,_ alpha:Double=1) {ctx.beginPath();ctx.addLines(between:points);ctx.closePath();ctx.setFillColor(color.cg(CGFloat(alpha)));ctx.fillPath()}
func text(_ str:String,_ x:Double,_ y:Double,_ size:Double,_ font:String,_ color:Col = ink,_ alpha:Double=1,_ tracking:Double=0,_ centered:Bool=false) {
    let f = CTFontCreateWithName(font as CFString,size,nil)
    let attrs:[NSAttributedString.Key:Any] = [NSAttributedString.Key(kCTFontAttributeName as String):f,NSAttributedString.Key(kCTForegroundColorAttributeName as String):color.cg(CGFloat(alpha)),NSAttributedString.Key(kCTKernAttributeName as String):tracking]
    let l = CTLineCreateWithAttributedString(NSAttributedString(string:str,attributes:attrs))
    let w = CTLineGetTypographicBounds(l,nil,nil,nil)
    ctx.saveGState();ctx.translateBy(x:x-(centered ? w/2 : 0),y:y+Double(CTFontGetAscent(f)));ctx.scaleBy(x:1,y:-1);ctx.textPosition = .zero;CTLineDraw(l,ctx);ctx.restoreGState()
}
// A fixed paper texture keeps the picture tactile without distracting motion.
let grainData = UnsafeMutablePointer<UInt8>.allocate(capacity:W*H*4)
var seed: UInt64 = 8392
for i in 0..<(W*H) { seed = seed &* 6364136223846793005 &+ 1; let v = UInt8((seed >> 33) % 10); grainData[i*4]=v;grainData[i*4+1]=v;grainData[i*4+2]=v;grainData[i*4+3]=9 }
let grainContext = CGContext(data:grainData,width:W,height:H,bitsPerComponent:8,bytesPerRow:W*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
let grain = grainContext.makeImage()!

func person(_ x:Double,_ baseline:Double,_ shirt:Col,_ skin:Col,_ phase:Double,_ reach:Double,_ lean:Double,_ variant:Int,_ t:Double) {
    let stride = sin(phase)*14*(1-reach)
    let bounce = abs(sin(phase))*3*(1-reach)
    let y = baseline-bounce
    let shoulderX = x+lean*12
    let sy = y-108+lean*10
    let hx = x+lean*16
    let hy = y-143+lean*10
    ellipse(x+2,y+3,32,5,ink,0.10)
    // Trousers and shoes; the feet settle as a person starts helping.
    line([p(x-9,y-55),p(x-11-stride*0.55,y-28),p(x-17+stride,y-3)],ink,13)
    line([p(x+10,y-55),p(x+13+stride*0.55,y-26),p(x+19-stride,y-3)],ink,13)
    line([p(x-19+stride,y-1),p(x-31+stride,y-1)],ink,9)
    line([p(x+18-stride,y-1),p(x+29-stride,y-1)],ink,9)
    // Softly angular jackets.
    polygon([p(shoulderX-19,sy-3),p(shoulderX+18,sy-3),p(x+23,y-53),p(x-24,y-53)],shirt)
    line([p(hx,hy+18),p(shoulderX,sy)],skin,13)
    // The two arms rise to share the circle. Outer people reach to their neighbours.
    let outer = variant >= 3
    let leftTarget = outer ? (variant == 3 ? p(x-48,y-68) : p(x-65,y-135)) : (variant == 2 ? p(x-58,y-202) : p(x-28,y-182))
    let rightTarget = outer ? (variant == 3 ? p(x+65,y-135) : p(x+48,y-68)) : (variant == 1 ? p(x+58,y-202) : p(x+32,y-184))
    let lhand = p(lerp(shoulderX-25,Double(leftTarget.x),reach),lerp(sy+46,Double(leftTarget.y),reach))
    let rhand = p(lerp(shoulderX+28,Double(rightTarget.x),reach),lerp(sy+40,Double(rightTarget.y),reach))
    let le = p(lerp(shoulderX-28,shoulderX-43,reach),lerp(sy+22,(variant == 3 ? sy+18 : sy-30),reach))
    let re = p(lerp(shoulderX+27,shoulderX+43,reach),lerp(sy+23,(variant == 4 ? sy+18 : sy-32),reach))
    line([p(shoulderX-15,sy+7),le,lhand],shirt,13)
    line([p(shoulderX+16,sy+8),re,rhand],shirt,13)
    ellipse(Double(lhand.x),Double(lhand.y),6,6,skin)
    ellipse(Double(rhand.x),Double(rhand.y),6,6,skin)
    ellipse(hx,hy,17,21,skin)
    // A distinctive silhouette for every member of the group.
    if variant == 0 {
        curve(p(hx-16,hy-2),p(hx-23,hy-31),p(hx+19,hy-30),p(hx+18,hy-7),ink,11)
    } else if variant == 1 {
        ellipse(hx-3,hy-16,17,10,ink)
        ellipse(hx-15,hy-5,5,13,ink)
    } else if variant == 2 {
        curve(p(hx-17,hy-7),p(hx-5,hy-26),p(hx+7,hy-27),p(hx+17,hy-9),paper,10)
    } else if variant == 3 {
        ellipse(hx,hy-18,17,8,ink)
        ellipse(hx-14,hy-29,9,10,ink)
    } else {
        line([p(hx-17,hy-9),p(hx+17,hy-9)],rust,8)
        ellipse(hx,hy-17,15,8,rust)
    }
    ellipse(hx+6,hy,1.5,1.8,ink)
    if reach > 0.6 && (variant != 0 || t > 4.6) {curve(p(hx+3,hy+9),p(hx+6,hy+11),p(hx+10,hy+10),p(hx+11,hy+7),ink,1.6,reach)}
}

func render(_ t:Double) {
    ctx.setFillColor(paper.cg());ctx.fill(CGRect(x:0,y:0,width:W,height:H))
    let lift = ease(2.3,6.2,t)
    let warm = ease(3.0,6.5,t)
    let final = ease(4.2,5.0,t)
    // Quiet publication-like frame.
    text("THE THINGS WE DO FOR EACH OTHER",76,57,15,"AvenirNext-DemiBold",ink,0.8,2.0)
    line([p(76,94),p(1004,94)],ink,1,0.2)
    // Small mark evolves from a point into a radiant star.
    for j in 0..<8 { let a = Double(j)*Double.pi/4;line([p(984+cos(a)*5,65+sin(a)*5),p(984+cos(a)*(9+lift*5),65+sin(a)*(9+lift*5))],ink,1.6) }
    let headingOut = 1-ease(3.4,4.1,t)
    text("Some days",74,123,91,"Baskerville",ink,headingOut)
    text("are heavy.",74,217,91,"Baskerville",ink,headingOut)
    let yy = (1-final)*12
    text("Make someone’s",74,123+yy,86,"Baskerville",ink,final)
    text("day lighter.",74,217+yy,86,"Baskerville",ink,final)

    // The shared ground is a single drawn line.
    curve(p(77,837),p(330,816),p(711,845),p(1003,826),ink,1.4,0.25)
    // Subtle warm halo expands as support arrives.
    let cx = lerp(524,540,lift), cy = lerp(511,492,lift), r = lerp(179,158,lift)
    for j in (0..<4).reversed() {ellipse(cx,cy,r+Double(j)*19+22,r+Double(j)*19+22,gold,warm*(0.018-Double(j)*0.003))}
    
    for j in 0..<18 {
        let a = Double(j)*2*Double.pi/18 + 0.02*sin(t)
        let inner = r+20+5*sin(t*1.2+Double(j))
        let outer = inner+(14+7*sin(Double(j)*2.2))*warm
        line([p(cx+cos(a)*inner,cy+sin(a)*inner),p(cx+cos(a)*outer,cy+sin(a)*outer)],gold,3,warm*0.75)
    }
    // People arrive, notice, and lift. Nobody disappears when the sun rises.
    let join1 = ease(1.25,3.15,t), join2 = ease(2.75,4.7,t)
    let join3 = ease(4.0,6.0,t), join4 = ease(4.35,6.35,t)
    let reach1 = ease(2.5,3.8,t), reach2 = ease(4.0,5.1,t)
    if t > 4.0 {person(lerp(-65,288,join3),827,blue,Col(0x6D493A),t*8.2, ease(5.2,6.5,t),0,3,t)}
    if t > 4.35 {person(lerp(1140,792,join4),827,lilac,Col(0xCE9471),t*8.2+1,ease(5.5,6.7,t),0,4,t)}
    if t > 1.25 {person(lerp(-62,397,join1),827,teal,Col(0xB27850),t*8,reach1,0,1,t)}
    if t > 2.75 {person(lerp(1140,683,join2),827,rust,Col(0xDDA780),t*8+1,reach2,0,2,t)}
    person(lerp(535,540,lift),827,coral,Col(0xE6B38E),0,lerp(0.64,1,lift),1-lift,0,t)

    // The heavy knot becomes a sun. Its contour relaxes from uneven to circular.
    var ball:[CGPoint] = []
    for k in 0..<180 { let a=Double(k)*2*Double.pi/180; let wobble=(sin(a*5+t*0.6)*2.8+cos(a*3-t*0.35)*2.3)*(1-warm);ball.append(p(cx+cos(a)*(r+wobble),cy+sin(a)*(r+wobble))) }
    polygon(ball,mix(ink,gold,warm))
    // A small light catches the top edge before the colour spreads.
    ctx.saveGState();ctx.beginPath();ctx.addLines(between:ball);ctx.closePath();ctx.clip()
    ellipse(cx-40,cy-60,r*0.95,r*0.8,mix(Col(0x3D4A5E),Col(0xFFD579),warm),0.32)
    // Sinuous fibres suggest the tangled weight of an ordinary hard day.
    for j in 0..<8 {
        let yy = cy-100+Double(j)*29
        curve(p(cx-r-10,yy+20*sin(Double(j))),p(cx-55,yy-80),p(cx+65,yy+85),p(cx+r+10,yy-15),paper,1.2,(1-warm)*0.15)
    }
    ctx.restoreGState()
    // Gentle motes escape as the burden lightens.
    if warm > 0 {
        for j in 0..<9 {
            let age = max(0,t-3.6-Double(j)*0.19)
            let a=Double(j)*2.399+0.5
            let rr=r+15+age*16
            let alpha = warm*max(0,1-age/3.1)*0.65
            ellipse(cx+cos(a)*rr,cy+sin(a)*rr,2.5,2.5,gold,alpha)
        }
    }
    // The hands rest in front of the circle, making the shared lift legible.
    let mx = lerp(535,540,lift), lean = 1-lift, reach = lerp(0.64,1,lift)
    let sx = mx+lean*12, sy = 719+lean*10
    ellipse(lerp(sx-25,mx-28,reach),lerp(sy+46,645,reach),6,7,Col(0xE6B38E))
    ellipse(lerp(sx+28,mx+32,reach),lerp(sy+40,643,reach),6,7,Col(0xE6B38E))
    // Palms wrap around the surface at each shared point of support.
    if t > 1.25 {
        let x = lerp(-62,397,join1)
        ellipse(lerp(x+28,x+58,reach1),lerp(759,625,reach1),6,6,Col(0xB27850))
    }
    if t > 2.75 {
        let x = lerp(1140,683,join2)
        ellipse(lerp(x-25,x-58,reach2),lerp(765,625,reach2),6,6,Col(0xDDA780))
    }
    // End card action, held long enough to read.
    let footer = ease(5.8,6.6,t)
    line([p(76,906),p(1004,906)],ink,1,0.2)
    text("Offer help. Accept help. Pass it on.",540,934,26,"AvenirNext-Medium",ink,footer,0,true)
    text("A LITTLE CARE CAN GO A LONG WAY",540,988,13,"AvenirNext-DemiBold",muted,footer,2.2,true)
    // Grain is applied last, so the type belongs to the same printed surface.
    ctx.saveGState();ctx.setBlendMode(.multiply);ctx.setAlpha(0.42);ctx.draw(grain,in:CGRect(x:0,y:0,width:W,height:H));ctx.restoreGState()
}

if CommandLine.arguments.count > 2 && CommandLine.arguments[1] == "--still" {
    render(Double(CommandLine.arguments[2])!)
    FileHandle.standardOutput.write(Data(bytesNoCopy:buffer,count:bytes,deallocator:.none))
} else {
    for i in 0..<frames {
        autoreleasepool {
            render(Double(i)/Double(fps))
            FileHandle.standardOutput.write(Data(bytesNoCopy:buffer,count:bytes,deallocator:.none))
        }
    }
}
