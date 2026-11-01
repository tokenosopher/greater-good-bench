import Foundation
import CoreGraphics
import CoreText
import ImageIO
import UniformTypeIdentifiers

let W = 960, H = 1080
struct Color {
    var r: CGFloat; var g: CGFloat; var b: CGFloat
    init(_ hex: UInt32) { r = CGFloat((hex >> 16) & 255)/255; g = CGFloat((hex >> 8) & 255)/255; b = CGFloat(hex & 255)/255 }
    func cg(_ a: CGFloat = 1) -> CGColor { CGColor(red:r, green:g, blue:b, alpha:a) }
}
let paper = Color(0xF4EEDF), ink = Color(0x233E41), gold = Color(0xEAAA46), coral = Color(0xC9664F), teal = Color(0x598D88), light = Color(0xFFF9E9)
func clamp(_ x: Double) -> Double { max(0,min(1,x)) }
func ease(_ x: Double) -> Double { let t=clamp(x); return t*t*(3-2*t) }
func lerp(_ a: Double,_ b: Double,_ p: Double)->Double { a+(b-a)*p }
func path(_ ctx: CGContext, _ pts: [(Double,Double)], _ color: Color, _ width: Double = 2, _ alpha: Double = 1) {
    guard let p=pts.first else{return}; ctx.beginPath();ctx.move(to:CGPoint(x:p.0,y:p.1)); for p in pts.dropFirst(){ctx.addLine(to:CGPoint(x:p.0,y:p.1))};ctx.setStrokeColor(color.cg(alpha));ctx.setLineWidth(width);ctx.setLineCap(.round);ctx.setLineJoin(.round);ctx.strokePath()
}
func ellipse(_ c: CGContext,_ x:Double,_ y:Double,_ w:Double,_ h:Double,_ col:Color,_ a:Double=1){ c.setFillColor(col.cg(a));c.fillEllipse(in:CGRect(x:x-w/2,y:y-h/2,width:w,height:h)) }
func text(_ c:CGContext,_ str:String,_ y:Double,_ size:Double,_ font:String,_ color:Color,_ alpha:Double=1,_ tracking:Double=0){
    c.saveGState();c.translateBy(x:0,y:y);c.scaleBy(x:1,y:-1)
    let f=CTFontCreateWithName(font as CFString,size,nil)
    let attr:[NSAttributedString.Key:Any]=[NSAttributedString.Key(kCTFontAttributeName as String):f,NSAttributedString.Key(kCTForegroundColorAttributeName as String):color.cg(alpha),NSAttributedString.Key(kCTKernAttributeName as String):tracking]
    let line=CTLineCreateWithAttributedString(NSAttributedString(string:str,attributes:attr));let w=CTLineGetTypographicBounds(line,nil,nil,nil)
    c.textPosition=CGPoint(x:(960-w)/2,y:0);CTLineDraw(line,c);c.restoreGState()
}
func person(_ c:CGContext,_ x:Double,_ foot:Double,_ s:Double,_ coat:Color,_ facing:Double,_ happy:Double,_ holding:Bool=false){
    c.saveGState();c.translateBy(x:x,y:foot);c.scaleBy(x:s,y:s)
    // Rounded silhouettes, with a little weight and hand-drawn asymmetry.
    path(c,[(-11,-48),(-14,-4),(-25,-4)],ink,10)
    path(c,[(12,-48),(18,-4),(28,-4)],ink,10)
    let body=CGMutablePath();body.move(to:CGPoint(x:-19,y:-114));body.addQuadCurve(to:CGPoint(x:20,y:-111),control:CGPoint(x:0,y:-126));body.addLine(to:CGPoint(x:27,y:-46));body.addQuadCurve(to:CGPoint(x:-28,y:-46),control:CGPoint(x:0,y:-37));body.closeSubpath();c.addPath(body);c.setFillColor(coat.cg());c.fillPath()
    let tilt=(1-happy)*6
    ellipse(c, facing*tilt,-141+tilt,42,45,ink)
    // Face is a tiny warm crescent, turned toward the other person.
    ellipse(c, facing*(11+tilt),-138+tilt,15,22,Color(0xD7AE85))
    ellipse(c, facing*(16+tilt),-142+tilt,3,3,ink)
    if holding { path(c,[(18,-103),(32,-81),(47,-88)],coat,13);ellipse(c,47,-88,10,10,Color(0xD7AE85)) }
    else { path(c,[(-facing*20,-103),(-facing*31,-78),(-facing*26,-66)],coat,12);ellipse(c,-facing*26,-66,9,9,Color(0xD7AE85)) }
    c.restoreGState()
}
func umbrella(_ c:CGContext,_ x:Double,_ apex:Double,_ width:Double,_ height:Double,_ shaft:Double,_ open:Double,_ col:Color){
    let w=width*(0.10+0.90*open), h=height*(1.14-0.14*open)
    path(c,[(x,apex-7),(x,apex+shaft-13)],ink,4)
    let hook=CGMutablePath();hook.move(to:CGPoint(x:x,y:apex+shaft-13));hook.addCurve(to:CGPoint(x:x-24,y:apex+shaft-13),control1:CGPoint(x:x,y:apex+shaft+9),control2:CGPoint(x:x-24,y:apex+shaft+9));c.addPath(hook);c.setStrokeColor(ink.cg());c.setLineWidth(4);c.strokePath()
    let canopy=CGMutablePath();canopy.move(to:CGPoint(x:x-w/2,y:apex+h));canopy.addCurve(to:CGPoint(x:x,y:apex),control1:CGPoint(x:x-w*0.43,y:apex+h*0.36),control2:CGPoint(x:x-w*0.22,y:apex-3));canopy.addCurve(to:CGPoint(x:x+w/2,y:apex+h),control1:CGPoint(x:x+w*0.22,y:apex-3),control2:CGPoint(x:x+w*0.43,y:apex+h*0.36))
    for i in (0..<4).reversed(){let a=x-w/2+w*Double(i)/4;let b=a+w/4;canopy.addQuadCurve(to:CGPoint(x:a,y:apex+h),control:CGPoint(x:(a+b)/2,y:apex+h-27*open))};canopy.closeSubpath();c.addPath(canopy);c.setFillColor(col.cg());c.fillPath()
    c.saveGState();c.addPath(canopy);c.clip();let panel=CGMutablePath();panel.move(to:CGPoint(x:x,y:apex));panel.addCurve(to:CGPoint(x:x-w/4,y:apex+h),control1:CGPoint(x:x-w/7,y:apex+20),control2:CGPoint(x:x-w/4,y:apex+h*0.7));panel.addLine(to:CGPoint(x:x-w/2,y:apex+h));panel.addLine(to:CGPoint(x:x-w/2,y:apex));panel.closeSubpath();c.addPath(panel);c.setFillColor(ink.cg(0.075));c.fillPath();c.restoreGState()
    for u in [-0.25,0.0,0.25]{let rib=CGMutablePath();rib.move(to:CGPoint(x:x,y:apex+2));rib.addQuadCurve(to:CGPoint(x:x+w*u,y:apex+h-1),control:CGPoint(x:x+w*u*0.8,y:apex+h*0.35));c.addPath(rib);c.setStrokeColor(ink.cg(0.22));c.setLineWidth(1.5);c.strokePath()}
    ellipse(c,x,apex-2,6,6,ink)
}
struct Neighbor {var x:Double;var y:Double;var s:Double;var delay:Double;var color:Color}
let neighbors=[Neighbor(x:211,y:579,s:0.49,delay:4.25,color:coral),Neighbor(x:751,y:579,s:0.49,delay:4.75,color:teal),Neighbor(x:116,y:780,s:0.43,delay:5.25,color:teal),Neighbor(x:844,y:780,s:0.43,delay:5.75,color:coral),Neighbor(x:295,y:915,s:0.44,delay:6.25,color:gold),Neighbor(x:665,y:915,s:0.44,delay:6.75,color:gold)]
func render(_ t:Double)->CGContext {
    let c=CGContext(data:nil,width:W,height:H,bitsPerComponent:8,bytesPerRow:W*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
    c.translateBy(x:0,y:Double(H));c.scaleBy(x:1,y:-1);c.setFillColor(paper.cg());c.fill(CGRect(x:0,y:0,width:W,height:H))
    // Extremely light paper tooth; fixed in time to keep the image calm.
    var seed:UInt64=7347
    for _ in 0..<5100 {seed=seed &* 6364136223846793005 &+ 1;let x=Double((seed>>24)%960);seed=seed &* 6364136223846793005 &+ 1;let y=Double((seed>>24)%1080);ellipse(c,x,y,1.1,1.1,ink,0.035)}
    text(c,"A SMALL ACT / A WIDER WORLD",66,14,"AvenirNext-DemiBold",ink,0.75,2.4)
    let titleChange=ease((t-3.8)/0.7)
    text(c,"A little room.",178,82,"Baskerville",ink,1-titleChange,-1.7)
    text(c,"A little kindness.",268,82,"Baskerville",ink,1-titleChange,-1.7)
    text(c,"Make room",178,88,"Baskerville",ink,titleChange,-1.7)
    text(c,"for each other.",268,88,"Baskerville",ink,titleChange,-1.7)
    // A sunlike disk grows around the shared shelter.
    let share=ease((t-1.25)/2.1)
    ellipse(c,lerp(430,480,share),629,lerp(240,475,share),lerp(260,475,share),gold,0.045+0.045*share)
    // Rain is quiet and sparse. Only the space beneath a canopy becomes dry.
    for i in 0..<115 {
        let xx=70+Double((i*137+41)%820);let yy=340+Double((i*83)%610)+t*43
        let y=340+(yy-340).truncatingRemainder(dividingBy:610)
        var sheltered=false
        let ux=lerp(430,490,share), uw=lerp(200,360,share)
        if xx>ux-uw/2 && xx<ux+uw/2 && y>555 && y<780 {sheltered=true}
        for n in neighbors {if t>n.delay+0.5 && abs(xx-n.x)<100*n.s && y>n.y-220*n.s && y<n.y+12{sheltered=true}}
        if !sheltered { path(c,[(xx,y),(xx-3,y+10)],teal,1.4,0.18) }
    }
    // Curved threads carry the gesture outward; dots make the motion legible.
    for (idx,n) in neighbors.enumerated(){
        let p=ease((t-(n.delay-0.65))/0.8)
        if p>0 {let startX=480.0;let startY=680.0;let endX=n.x;let endY=n.y-90*n.s;let bend=(idx%2==0 ? -65.0:65.0)
            var points:[(Double,Double)]=[]
            for j in 0...70 {let u=Double(j)/70*p;let xx=lerp(startX,endX,u)+sin(u*Double.pi)*bend;let yy=lerp(startY,endY,u)+sin(u*Double.pi)*30;points.append((xx,yy))}
            c.saveGState();c.setLineDash(phase:0,lengths:[2,8]);path(c,points,gold,2,0.6);c.restoreGState()
            if p<1, let last=points.last {ellipse(c,last.0,last.1,8,8,gold)}
        }
    }
    for n in neighbors {
        let appear=ease((t-3.65)/0.85), opened=ease((t-n.delay)/0.75)
        if appear<=0 {continue};c.saveGState();c.setAlpha(appear)
        ellipse(c,n.x,n.y+4,200*n.s,20*n.s,ink,0.07)
        ellipse(c,n.x,n.y-106*n.s,255*n.s,255*n.s,gold,0.12*opened)
        person(c,n.x-32*n.s,n.y,n.s,teal,1,opened)
        person(c,n.x+39*n.s,n.y,n.s,coral,-1,opened)
        if opened>0 {umbrella(c,n.x,n.y-260*n.s,250*n.s,73*n.s,174*n.s,opened,n.color)}
        c.restoreGState()
    }
    ellipse(c,485,775,274,23,ink,0.09)
    // The second figure first stands in the rain. Both move toward each other.
    let bob=sin(share*Double.pi*4)*3*(1-share)
    person(c,lerp(578,547,share),765+bob,1.0,coral,-1,share)
    person(c,lerp(383,442,share),765-bob,1.0,teal,1,1,true)
    umbrella(c,lerp(430,490,share),472,lerp(200,360,share),90,211,1,gold)
    let footer=ease((t-7.35)/0.7)
    text(c,"Notice. Ask. Listen.",998,27,"AvenirNext-Medium",ink,footer,0.3)
    text(c,"CARE IS SOMETHING WE CAN PASS ON",1034,11,"AvenirNext-DemiBold",ink,footer*0.66,2.1)
    // Unobtrusive time marks show the three movements of the film.
    for j in 0..<3 {let active=t >= [0.0,1.25,4.25][j];c.setFillColor((active ? gold : ink).cg(active ? 0.9:0.12));c.fill(CGRect(x:435+j*34,y:1060,width:22,height:2))}
    return c
}
let args=CommandLine.arguments
if args.count>1 && args[1]=="still" {
    let t=Double(args[2])!;let c=render(t);let image=c.makeImage()!;let url=URL(fileURLWithPath:args[3]);let dst=CGImageDestinationCreateWithURL(url as CFURL,UTType.jpeg.identifier as CFString,1,nil)!;CGImageDestinationAddImage(dst,image,[kCGImageDestinationLossyCompressionQuality:0.9] as CFDictionary);CGImageDestinationFinalize(dst)
} else {
    let out=FileHandle.standardOutput
    for f in 0..<300 {autoreleasepool {let c=render(Double(f)/30);out.write(Data(bytes:c.data!,count:W*H*4))}}
}
