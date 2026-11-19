import CoreText
import Foundation

// Convert the two captions to outlines so the poster has no font dependencies.
let font = CTFontCreateWithName("IowanOldStyle-Roman" as CFString, 48, nil)
for caption in CommandLine.arguments.dropFirst() {
    let line = CTLineCreateWithAttributedString(NSAttributedString(
        string: caption,
        attributes: [NSAttributedString.Key(kCTFontAttributeName as String): font]
    ))
    var outline = ""
    for run in CTLineGetGlyphRuns(line) as! [CTRun] {
        let count = CTRunGetGlyphCount(run)
        var glyphs = [CGGlyph](repeating: 0, count: count)
        var positions = [CGPoint](repeating: .zero, count: count)
        CTRunGetGlyphs(run, CFRange(location: 0, length: 0), &glyphs)
        CTRunGetPositions(run, CFRange(location: 0, length: 0), &positions)
        for (glyph, position) in zip(glyphs, positions) {
            guard let path = CTFontCreatePathForGlyph(font, glyph, nil) else { continue }
            func point(_ p: CGPoint) -> String {
                return String(format: "%.2f %.2f", Double(position.x + p.x), Double(-position.y - p.y))
            }
            path.applyWithBlock { element in
                let p = element.pointee.points
                switch element.pointee.type {
                case .moveToPoint: outline += "M" + point(p[0])
                case .addLineToPoint: outline += "L" + point(p[0])
                case .addQuadCurveToPoint: outline += "Q" + point(p[0]) + " " + point(p[1])
                case .addCurveToPoint: outline += "C" + point(p[0]) + " " + point(p[1]) + " " + point(p[2])
                case .closeSubpath: outline += "Z"
                @unknown default: break
                }
            }
        }
    }
    print(outline)
}
