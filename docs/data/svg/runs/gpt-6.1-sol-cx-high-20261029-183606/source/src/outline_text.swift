import Foundation
import CoreText
import CoreGraphics

// Convert installed font glyphs to SVG paths so the poster is self-contained.
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let requests = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as! [[String: Any]]
var result: [String: Any] = [:]
func n(_ v: CGFloat) -> String { String(format: "%.3f", Double(v)) }
for item in requests {
    let id = item["id"] as! String
    let font = CTFontCreateWithName(item["font"] as! CFString, item["size"] as! CGFloat, nil)
    let line = CTLineCreateWithAttributedString(NSAttributedString(string: item["text"] as! String, attributes: [NSAttributedString.Key(kCTFontAttributeName as String): font]))
    let width = CTLineGetTypographicBounds(line, nil, nil, nil)
    var data = ""
    for runObj in CTLineGetGlyphRuns(line) as NSArray {
        let run = runObj as! CTRun
        let count = CTRunGetGlyphCount(run)
        var glyphs = [CGGlyph](repeating: 0, count: count)
        var positions = [CGPoint](repeating: .zero, count: count)
        CTRunGetGlyphs(run, CFRangeMake(0, 0), &glyphs)
        CTRunGetPositions(run, CFRangeMake(0, 0), &positions)
        for i in 0..<count {
            guard let path = CTFontCreatePathForGlyph(font, glyphs[i], nil) else { continue }
            let dx = positions[i].x
            let dy = positions[i].y
            path.applyWithBlock { element in
                let e = element.pointee
                func p(_ i: Int) -> String { n(e.points[i].x + dx) + " " + n(-(e.points[i].y + dy)) }
                switch e.type {
                case .moveToPoint: data += "M" + p(0)
                case .addLineToPoint: data += "L" + p(0)
                case .addQuadCurveToPoint: data += "Q" + p(0) + " " + p(1)
                case .addCurveToPoint: data += "C" + p(0) + " " + p(1) + " " + p(2)
                case .closeSubpath: data += "Z"
                @unknown default: break
                }
            }
        }
    }
    result[id] = ["path": data, "width": width]
}
let out = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
try out.write(to: URL(fileURLWithPath: CommandLine.arguments[2]))
