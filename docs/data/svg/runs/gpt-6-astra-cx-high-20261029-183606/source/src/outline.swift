import Foundation
import CoreText
import CoreGraphics

let input = FileHandle.standardInput.readDataToEndOfFile()
let items = try JSONSerialization.jsonObject(with: input) as! [[String: Any]]
func n(_ v: CGFloat) -> String { String(format: "%.3f", Double(v)) }
var result: [String] = []
for item in items {
    let text = item["text"] as! String
    let size = item["size"] as! Double
    let font = CTFontCreateWithName((item["font"] as! String) as CFString, size, nil)
    let attrs: [NSAttributedString.Key: Any] = [NSAttributedString.Key(kCTFontAttributeName as String): font, NSAttributedString.Key(kCTKernAttributeName as String): item["tracking"] as? Double ?? 0]
    let line = CTLineCreateWithAttributedString(NSAttributedString(string: text, attributes: attrs))
    let width = CTLineGetTypographicBounds(line, nil, nil, nil)
    var x = item["x"] as! Double
    if item["anchor"] as? String == "middle" { x -= width / 2 }
    if item["anchor"] as? String == "end" { x -= width }
    let y = item["y"] as! Double
    var d = ""
    for run in CTLineGetGlyphRuns(line) as! [CTRun] {
        let count = CTRunGetGlyphCount(run)
        var glyphs = [CGGlyph](repeating: 0, count: count)
        var positions = [CGPoint](repeating: .zero, count: count)
        CTRunGetGlyphs(run, CFRange(location: 0, length: 0), &glyphs)
        CTRunGetPositions(run, CFRange(location: 0, length: 0), &positions)
        for i in 0..<count {
            guard let path = CTFontCreatePathForGlyph(font, glyphs[i], nil) else { continue }
            let p = positions[i]
            func pt(_ v: CGPoint) -> String { "\(n(v.x+p.x)) \(n(v.y+p.y))" }
            path.applyWithBlock { ptr in
                let e = ptr.pointee
                switch e.type {
                case .moveToPoint: d += "M" + pt(e.points[0])
                case .addLineToPoint: d += "L" + pt(e.points[0])
                case .addQuadCurveToPoint: d += "Q" + pt(e.points[0]) + " " + pt(e.points[1])
                case .addCurveToPoint: d += "C" + pt(e.points[0]) + " " + pt(e.points[1]) + " " + pt(e.points[2])
                case .closeSubpath: d += "Z"
                @unknown default: break
                }
            }
        }
    }
    result.append("<path fill=\"\(item["color"] as! String)\" transform=\"translate(\(x) \(y)) scale(1 -1)\" d=\"\(d)\"/>")
}
let out = try JSONSerialization.data(withJSONObject: result)
FileHandle.standardOutput.write(out)
