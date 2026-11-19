"""Draw the Make Room poster with vector shapes, dry ink and outlined type."""

from math import cos, sin, radians
from pathlib import Path
from random import Random
from subprocess import check_output
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
PAGE_W, PAGE_H = 1080, 1380
ART_W, ART_H = 976, 916
PAPER = "#f4e8ce"
INK = "#19182f"
parts = []


def emit(markup):
    parts.append(markup.strip())


def num(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def path(d, fill="none", stroke="none", width=1, extra=""):
    emit(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" {extra}/>')


def ellipse(x, y, rx, ry, fill, extra=""):
    emit(f'<ellipse cx="{num(x)}" cy="{num(y)}" rx="{num(rx)}" ry="{num(ry)}" fill="{fill}" {extra}/>')


def grain(w, h, density, seed, fill, opacity):
    """Collect short, irregular ink marks into a single compact SVG path."""
    roll = Random(seed)
    marks = []
    for _ in range(density):
        x, y = roll.randrange(w), roll.randrange(h)
        length = roll.choice([1, 1, 1, 2, 3])
        tilt = roll.choice([-1, 0, 0, 1])
        marks.append(f"M{x} {y}l{length} {tilt}")
    path("".join(marks), stroke=fill, width=".8", extra=f'opacity="{opacity}"')


def draw_heading():
    # Hand-drawn display letters with the same cap line and compact spacing.
    glyphs = {
        "M": "M0 120V0H34L58 50L83 0H116V120H85V55L64 101H51L30 55V120Z",
        "A": "M0 120L37 0H72L109 120H76L70 96H37L31 120ZM43 73H64L54 33Z",
        "K": "M0 120V0H32V47L70 0H108L61 54L111 120H72L40 77L32 86V120Z",
        "E": "M0 120V0H91V26H32V46H84V71H32V94H93V120Z",
        "R": "M0 120V0H57C86 0 101 14 101 39C101 57 94 68 80 74L108 120H72L47 79H32V120ZM32 25V54H54C64 54 69 49 69 39C69 30 64 25 54 25Z",
        "O": "M57 -2C96 -2 114 21 114 60C114 99 96 122 57 122C18 122 0 99 0 60C0 21 18 -2 57 -2ZM57 25C40 25 33 36 33 60C33 84 40 95 57 95C74 95 81 84 81 60C81 36 74 25 57 25Z",
    }
    for letter, x in zip("MAKEROOM", [0, 130, 250, 370, 500, 619, 747, 875]):
        path(glyphs[letter], INK, extra=f'transform="translate({x})" fill-rule="evenodd"')


def draw_floor():
    emit(f"""
    <rect width="{ART_W}" height="{ART_H}" fill="#242756"/>
    <path d="M0 598L461 0H976V916H0Z" fill="#292d61"/>
    <path d="M0 744L622 0H711L60 916H0Z" fill="#33366c" opacity=".48"/>
    <path d="M0 731L622 0M45 916L735 0M446 916L938 0M0 609L976 814M0 489L976 671M0 376L976 540M0 273L976 413M0 172L976 283M0 81L976 165" fill="none" stroke="#7e87bf" opacity=".15" stroke-width="1.4"/>
    <ellipse cx="490" cy="652" rx="455" ry="233" fill="#1e204c"/>
    <ellipse cx="488" cy="629" rx="454" ry="232" fill="#3d437d"/>
    <ellipse cx="488" cy="629" rx="454" ry="232" fill="url(#floor-dots)"/>
    <ellipse cx="488" cy="629" rx="431" ry="215" fill="none" stroke="#828bc1" stroke-width="2"/>
    <ellipse cx="488" cy="629" rx="421" ry="208" fill="none" stroke="#8b94c7" opacity=".6" stroke-dasharray="2 6"/>
    <path d="M101 665C174 746 322 789 480 788C643 789 790 741 880 655" stroke="#9ca4d3" stroke-width="1.5" fill="none" opacity=".38"/>
    <path d="M285 809C396 829 534 834 657 814C691 808 693 792 662 789C554 783 483 773 367 774C324 775 275 788 285 809Z" fill="#292d60"/>
    <path d="M324 801C390 811 493 818 620 805" stroke="#7684b6" opacity=".35" fill="none" stroke-width="1.5" stroke-dasharray="2 5"/>
    """)


def draw_support():
    emit("""
    <path d="M180 615C184 560 294 517 480 511C648 505 783 548 803 609C824 669 695 725 503 732C326 739 174 686 180 615Z" fill="#1b1e46" opacity=".75"/>
    <path d="M180 615C184 560 294 517 480 511C648 505 783 548 803 609C824 669 695 725 503 732C326 739 174 686 180 615Z" fill="url(#shadow-hatch)" opacity=".55"/>
    <path d="M361 654C400 632 453 621 491 623C535 625 592 640 613 657L614 672C575 693 532 709 486 709C442 710 388 692 360 671Z" fill="#1b1b3b" stroke="#17182f" stroke-width="3"/>
    <path d="M361 654C397 643 438 625 491 624C542 625 577 640 613 657C571 676 537 685 487 687C435 685 396 674 361 654Z" fill="#656faf"/>
    <path d="M431 511L548 511L543 656Q485 680 436 656Z" fill="#6a74b4" stroke="#1b1b38" stroke-width="4"/>
    <path d="M499 521L548 516L543 656Q522 667 497 667Z" fill="#383a78"/>
    <path d="M444 546L447 652M455 548L458 657M470 550L471 659M485 550L485 662" stroke="#b0b8dc" opacity=".45" stroke-width="2"/>
    """)


def draw_left_chair():
    emit("""
    <path d="M79 545Q114 571 203 581L215 571L171 553Z" fill="#20234b"/>
    <path d="M101 462L87 551M174 480L164 569M226 487L229 554M146 466L123 548" stroke="#1c1d40" stroke-width="12" stroke-linecap="round"/>
    <path d="M101 463L87 551M174 480L164 569" stroke="#8b98d2" stroke-width="5" stroke-linecap="round"/>
    <path d="M82 406Q88 396 100 400L124 404L146 463L186 457Q197 460 200 474L194 489L114 479Q106 477 104 467Z" fill="#4d5895" stroke="#1c1b38" stroke-width="4"/>
    <path d="M85 408L109 463Q113 473 125 473L189 481" stroke="#a1aad6" stroke-width="3" fill="none"/>
    """)


def draw_right_chair():
    emit("""
    <path d="M774 538Q816 535 882 552L917 573Q895 588 822 578Z" fill="#262959"/>
    <path d="M803 478L798 555M870 488L882 567M912 463L923 543M839 480L846 544" stroke="#1c1d40" stroke-width="12" stroke-linecap="round"/>
    <path d="M870 488L882 567M912 463L923 543" stroke="#8490c5" stroke-width="5" stroke-linecap="round"/>
    <path d="M912 401L903 459Q901 473 888 480L812 499L794 485L809 466L869 447L891 399Z" fill="#505d9d" stroke="#1c1b38" stroke-width="4"/>
    <path d="M907 405L892 460L817 487" stroke="#97a1d1" stroke-width="3" fill="none"/>
    """)


def draw_back_left():
    emit("""
    <g stroke="#211b3d" stroke-width="4" stroke-linejoin="round">
      <path d="M204 350L182 278Q180 263 194 258L227 249L246 320Z" fill="#6673b0"/>
      <path d="M187 271L210 339" stroke="#afb9e1" stroke-width="2.5"/>
      <path d="M241 242C209 253 206 270 203 300L210 355L331 353L369 327L344 271Q333 247 296 238Z" fill="#6a76c8"/>
      <path d="M241 242C209 253 206 270 203 300L210 355L331 353L369 327L344 271Q333 247 296 238Z" fill="url(#blue-dots)" stroke="none"/>
      <path d="M245 233L249 263Q269 283 299 255L294 218Z" fill="#a9594f"/>
      <path d="M246 249Q270 269 299 245L303 254Q267 286 243 260Z" fill="#c1c6ec"/>
      <path d="M240 159Q269 133 307 160Q320 172 319 197L331 211Q334 217 321 218L321 235Q319 253 299 252Q270 246 250 227Q225 212 229 181Z" fill="#c37a62"/>
      <path d="M295 175Q277 179 267 198L260 220Q248 226 243 217C226 219 219 201 224 192C213 185 214 169 222 165C214 154 225 143 235 145C234 133 252 128 260 135C267 124 281 128 287 136C302 128 317 139 314 149C331 151 333 169 322 176Q306 180 295 175Z" fill="#222040"/>
      <path d="M266 203Q259 192 253 196Q245 201 252 213Q256 221 264 220" fill="#b5725e" stroke-width="2.3"/>
      <path d="M302 193Q309 191 316 194M311 229Q315 229 321 227" fill="none" stroke-width="2.4" stroke-linecap="round"/>
      <ellipse cx="312" cy="200.5" rx="2.25" ry="2.9" fill="#211b3d" stroke="none"/>
      <path d="M215 269Q228 262 245 273L267 310L246 331L218 312" fill="#8b96db"/>
      <path d="M335 267Q330 277 335 298L338 312L360 321" fill="none" stroke="#3f4c95" stroke-width="2.5"/>
    </g>
    <path d="M232 157C244 145 269 141 287 149M226 176Q229 167 238 166M242 185Q247 171 266 166M279 155Q291 152 305 158" fill="none" stroke="#7572ad" opacity=".62" stroke-width="2.4" stroke-linecap="round"/>
    <path d="M280 222Q292 237 308 238" fill="none" stroke="#eea287" opacity=".76" stroke-width="2.2"/>
    """)


def draw_back_right():
    emit("""
    <g stroke="#211b3d" stroke-width="4" stroke-linejoin="round">
      <path d="M728 340L747 250Q745 240 735 239L700 231L684 315Z" fill="#636da9"/>
      <path d="M739 249L723 319" stroke="#a9afdc" stroke-width="2.5"/>
      <path d="M592 248Q610 233 640 226L675 226Q715 240 725 269L737 344L587 350L568 316Z" fill="#c5c8e8"/>
      <path d="M592 248Q610 233 640 226L675 226Q715 240 725 269L737 344L587 350L568 316Z" fill="url(#blue-dots)" stroke="none"/>
      <path d="M612 254Q594 263 591 290L591 321L570 321M672 262Q696 261 703 279L715 321" stroke="#737cb5" stroke-width="2.5" fill="none"/>
      <path d="M628 223L627 245Q647 259 672 236L661 205Z" fill="#d89975"/>
      <path d="M627 235L620 246L629 261L643 249L657 260L679 237L671 230Q649 248 643 249Q633 243 627 235Z" fill="#e9e7f1" stroke-width="2.5"/>
      <path d="M609 155Q637 134 668 158C687 172 685 200 669 219Q648 236 630 232C607 228 602 216 604 207L592 205Q588 204 593 198L604 184Z" fill="#efb694"/>
      <path d="M606 174Q595 163 605 151Q619 145 634 139Q662 130 681 149Q698 163 692 185Q687 205 668 216L662 201C672 194 671 183 665 181Q658 177 652 189L645 185L641 168Q625 178 606 174Z" fill="#e7ddce"/>
      <path d="M606 216Q613 217 617 213" fill="none" stroke-width="2.3" stroke-linecap="round"/>
      <ellipse cx="609.5" cy="189.8" rx="2" ry="2.5" fill="#211b3d" stroke="none"/>
      <path d="M601 181L620 183L619 195L605 197L600 190Z" fill="none" stroke-width="2.4"/>
      <path d="M619 185L654 184" stroke-width="2.4"/>
    </g>
    <path d="M609 156Q626 155 640 146Q649 142 661 146M610 162Q626 163 643 155M663 155Q684 164 676 188M678 153Q688 160 687 173" fill="none" stroke="#9894a4" stroke-width="2" stroke-linecap="round"/>
    <path d="M639 273L639 294M647 274L647 288M653 306L653 318" fill="none" stroke="#f1e9ee" stroke-width="2.4"/>
    """)


def draw_table():
    emit("""
    <path d="M192 428C192 340 324 273 488 273C651 273 784 342 784 428V446C784 531 653 601 488 601C325 601 192 533 192 446Z" fill="#b8765b" stroke="#201d37" stroke-width="5"/>
    <path d="M192 435C216 510 335 575 489 575C622 575 739 528 783 452L781 470C750 548 630 601 488 601C326 601 192 531 192 446Z" fill="url(#edge-hatch)"/>
    <ellipse cx="488" cy="424" rx="296" ry="153" fill="#f2d9ac" stroke="#201d37" stroke-width="5"/>
    <ellipse cx="488" cy="424" rx="296" ry="153" fill="url(#table-dots)"/>
    <ellipse cx="488" cy="424" rx="286" ry="143" fill="none" stroke="#b98872" stroke-width="1.25" opacity=".73"/>
    <path d="M196 440C225 516 345 574 488 575C638 575 754 518 781 442" stroke="#fff0c9" stroke-width="2.1" fill="none"/>
    <path d="M264 482Q336 520 468 527Q608 532 719 471M269 382Q329 349 424 340M588 336Q671 349 706 379" stroke="#b98769" stroke-width="1.4" fill="none" opacity=".58" stroke-dasharray="2 6"/>
    """)


def draw_paper():
    emit("""
    <path d="M394 457L451 382L587 403L546 476Z" fill="#9b694f" opacity=".3"/>
    <path d="M389 450L443 375L580 394L539 470Z" fill="#fbefd4" stroke="#8d625a" stroke-width="1.8"/>
    <path d="M525 468L539 470L552 446L536 450Z" fill="#d5ab87"/>
    <path d="M456 397L538 408M448 409L517 418M439 421L522 432M430 434L482 441" fill="none" stroke="#6370a3" stroke-width="2" stroke-linecap="round"/>
    <path d="M520 426L532 429M512 440L525 442" stroke="#bd6f54" stroke-width="2.2" stroke-linecap="round"/>
    <path d="M559 454L592 457L617 417" stroke="#986444" stroke-width="3.5" fill="none" opacity=".35"/>
    <path d="M593 452L613 410L616 409L615 414L596 455L590 460Z" fill="#454d90"/>
    <path d="M590 460L596 455L593 452Z" fill="#8c5f4a"/>
    """)


def draw_mug(x, y, color, rim):
    emit(f'<g transform="translate({x} {y})">')
    ellipse(5, 14, 24, 9, "#875a55", 'opacity=".30"')
    path("M13 -10Q30 -12 27 0Q26 10 14 8L14 3Q22 4 22 -1Q23 -6 15 -4Z", color, "#47324b", 1.5)
    path("M-17 -12L-14 10Q-13 17 0 17Q15 17 16 10L18 -12Z", color, "#47324b", 1.5)
    ellipse(.5, -12, 17.5, 7.2, rim, 'stroke="#47324b" stroke-width="1.5"')
    path("M-13 -10Q1 -16 14 -10Q5 -4 -6 -6Z", "#493049")
    path("M-11 -2L-9 9", stroke="#f7e3bd", width=1.4, extra='opacity=".76" stroke-linecap="round"')
    emit("</g>")


def draw_back_arms():
    emit("""
    <g stroke="#211b3d" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round">
      <path d="M236 303Q243 298 259 301L287 325L325 333L319 351L272 350L240 332Q226 321 236 303Z" fill="#8c97db"/>
      <path d="M312 331Q326 327 341 331L359 340Q365 345 358 348L345 346Q351 350 345 353L330 353L315 350Z" fill="#c37a62"/>
      <path d="M251 308L274 330L308 337M328 338L345 344" fill="none" stroke-width="1.8" opacity=".55"/>
      <path d="M609 257Q592 262 587 282L583 307Q580 316 568 321L545 333L555 351Q584 347 609 328Q616 322 617 312L622 283" fill="#b5bbe6"/>
      <path d="M551 330Q533 330 521 334L503 344Q499 350 506 351L522 347L510 356Q509 361 516 361L535 353L554 351Z" fill="#efb694"/>
      <path d="M595 319L579 334L562 342M521 348L531 343" fill="none" stroke-width="1.8" opacity=".48"/>
      <path d="M695 280Q708 281 716 302L723 327Q725 341 711 348L657 367L648 351L691 326L685 307" fill="#c6cbea"/>
      <path d="M649 351Q638 349 630 354L618 364Q614 371 621 373L638 370L656 369Z" fill="#efb694"/>
      <path d="M711 336L668 357M624 365L638 359" fill="none" stroke-width="1.8" opacity=".48"/>
    </g>
    """)


def draw_left_person():
    emit("""
    <g stroke="#201b38" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">
      <path d="M155 472L235 467Q264 488 255 515L234 562L212 568L203 554L217 515L152 522Q124 513 125 492Z" fill="#534e86"/>
      <path d="M205 552L232 555L248 569Q250 580 238 584L193 580Q185 577 191 566Z" fill="#aaa9cb"/>
      <path d="M191 573L237 580L246 575" fill="none" stroke-width="2"/>
      <path d="M134 390Q111 395 104 411Q92 436 112 480L136 507Q174 509 211 481L193 442Q184 404 172 395Z" fill="#7774b3"/>
      <path d="M134 390Q111 395 104 411Q92 436 112 480L136 507Q174 509 211 481L193 442Q184 404 172 395Z" fill="url(#blue-dots)" stroke="none"/>
      <path d="M156 375L146 397Q145 410 170 418L181 400L182 377Z" fill="#e0a083"/>
      <path d="M134 328Q151 305 178 311Q203 315 213 345L227 352Q232 358 222 363L219 375Q215 391 196 390L172 383Q144 385 130 360Z" fill="#efb796"/>
      <path d="M133 351Q118 368 111 391Q105 414 78 413Q68 412 70 400Q83 393 84 373Q84 345 108 338L130 333Z" fill="#292347"/>
      <path d="M127 352Q110 340 123 321Q140 299 169 303Q195 305 207 326Q202 334 187 336Q178 338 175 357L168 362Q155 344 149 359Q145 370 160 375L157 382Q141 387 129 374Z" fill="#282345"/>
      <path d="M202 345Q206 341 212 343M218 371Q212 373 207 369" fill="none" stroke-width="2.2"/>
      <ellipse cx="211" cy="351" rx="2.2" ry="2.7" fill="#211b3d" stroke="none"/>
      <path d="M114 415Q136 403 154 422L176 445L222 431L230 453Q202 469 171 476Q158 479 147 470L123 450" fill="#9996ce"/>
      <path d="M221 431Q233 423 245 424L263 427Q270 431 263 435L250 436L264 439Q270 442 264 446L250 449L230 453Z" fill="#efb796" stroke-width="3"/>
      <path d="M153 426L174 453L214 441M127 456Q139 472 149 478M152 493Q169 495 186 483M238 432L250 436" fill="none" stroke="#4c497e" stroke-width="2.1"/>
    </g>
    <path d="M91 398Q97 391 102 368Q107 352 120 348M125 334Q142 310 165 315M130 344Q144 324 168 325Q178 326 186 320M138 352Q147 339 161 337" fill="none" stroke="#867db0" stroke-width="2" stroke-linecap="round"/>
    <path d="M164 377A7 7 0 1 1 153 372" stroke="#f5d992" stroke-width="3.7" fill="none" stroke-linecap="round"/>
    <path d="M120 425L151 415M123 433L157 424M129 441L163 432M136 449L169 440M145 458L172 447M153 465L177 454" fill="none" stroke="#d0c8e8" stroke-width="1.8" opacity=".73"/>
    """)


def draw_right_person():
    emit("""
    <g stroke="#211b3d" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">
      <path d="M820 465L871 479Q870 507 839 521L785 526L776 569L749 570Q737 551 744 511Q747 496 762 490Z" fill="#7b83ae"/>
      <path d="M749 553L778 560L778 574Q775 581 761 583L723 580Q715 576 720 569L740 563Z" fill="#c3bfd9"/>
      <path d="M721 574Q740 580 768 577" fill="none" stroke-width="2"/>
      <path d="M807 382Q843 381 868 411Q885 434 877 476Q857 503 811 498L797 459L783 425Q782 399 807 382Z" fill="#5160ae"/>
      <path d="M807 382Q843 381 868 411Q885 434 877 476Q857 503 811 498L797 459L783 425Q782 399 807 382Z" fill="url(#light-dots)" stroke="none"/>
      <path d="M792 362L817 352L830 385Q826 403 806 409L792 397Z" fill="#935449"/>
      <path d="M788 386L796 400L807 409Q830 404 833 385L843 391Q839 418 807 421Q797 416 788 401Z" fill="#91a0df" stroke-width="2.7"/>
      <path d="M795 297Q832 293 846 322Q853 345 835 369L814 382Q792 390 780 377Q775 369 772 358L763 353Q758 348 766 344L775 329Q774 305 795 297Z" fill="#a75f52"/>
      <path d="M775 330Q774 319 777 309Q786 284 817 286Q845 288 853 310Q862 335 848 354L833 367Q824 358 826 343Q815 336 812 324Q798 333 775 330Z" fill="#27203f"/>
      <path d="M824 343Q832 334 839 340Q845 346 836 356" fill="#a75f52" stroke-width="2.2"/>
      <path d="M777 337Q782 337 787 340M777 366Q782 369 789 365" fill="none" stroke-width="2.1"/>
      <ellipse cx="780" cy="345.5" rx="2.1" ry="2.8" fill="#211b3d" stroke="none"/>
      <path d="M819 422Q815 409 800 409Q789 409 778 424L752 453L705 469L709 493Q746 492 776 479L815 451" fill="#737fc4"/>
      <path d="M706 470L677 466L661 457Q651 458 654 466L663 476L638 476Q629 477 633 483L642 487L633 491Q631 497 642 499L670 501Q687 501 711 492Z" fill="#b8725d" stroke-width="3"/>
      <path d="M644 487L668 489M653 478L673 482M716 482L764 467L795 437M832 464Q842 480 856 483" fill="none" stroke="#343c79" stroke-width="2.2" opacity=".7"/>
    </g>
    <path d="M785 315Q797 299 808 300M794 317Q808 298 823 300M812 316Q824 304 835 310M825 324Q838 315 848 327M835 331Q844 328 849 335" fill="none" stroke="#8b7ba1" opacity=".7" stroke-width="1.9" stroke-linecap="round"/>
    <path d="M787 354Q800 350 808 357M790 371Q797 377 807 373" fill="none" stroke="#d48c72" stroke-width="2.25" stroke-linecap="round"/>
    <path d="M803 418L780 447M809 425L790 450M812 432L800 449" stroke="#aab4e8" opacity=".6" stroke-width="1.8"/>
    """)


def draw_invitation():
    emit("""
    <path d="M416 630Q490 649 567 630L627 784Q634 808 603 816Q498 845 375 811Q347 804 359 784Z" fill="url(#amber-dots)"/>
    <path d="M385 722Q489 763 604 719M368 770Q491 819 623 765" fill="none" stroke="#edb077" stroke-width="2" stroke-dasharray="2 7" opacity=".50" stroke-linecap="round"/>
    """)


def draw_open_chair():
    # Orthographic projection of a bent-plywood chair. Local positive y is
    # toward the backrest and positive z lifts pieces off the floor.
    angle = radians(-19)

    def project(point):
        x, y, z = point
        return (490 + 1.075 * (x * cos(angle) - y * sin(angle)),
                783 + 1.075 * (.52 * (x * sin(angle) + y * cos(angle)) - .854 * z))

    def coordinates(point):
        return " ".join(num(value) for value in project(point))

    def render(commands, color, stroke="none", width=1, extra=""):
        d = "".join(command + " ".join(coordinates(p) for p in points)
                    for command, *points in commands)
        path(d, color, stroke, width, extra)

    stroke = "#352039"
    rounded = 'stroke-linecap="round"'
    for x in (-65, 65):
        front_foot = (x * 1.16, -69, 4)
        front_leg = [("M", front_foot), ("L", (x, -53, 125))]
        render(front_leg, "none", stroke, 16, rounded)
        render(front_leg, "none", "#b53f32", 10, rounded)
        render([("M", (x * 1.16 - 1, -70, 8)), ("L", (x - 1, -54, 121))],
               "none", "#f67750", 2.3, rounded)

    for x in (-68, 68):
        rear_leg = [("M", (x * 1.18, 75, 4)), ("L", (x, 58, 125)),
                    ("Q", (x, 62, 163), (x, 83, 219))]
        render(rear_leg, "none", stroke, 17, rounded)
        render(rear_leg, "none", "#e65439", 11, rounded)
        render([("M", (x * 1.18 - 1, 73, 8)), ("L", (x - 1, 56, 124)),
                ("Q", (x - 1, 59, 166), (x - 1, 80, 214))], "none", "#ff9d66", 2.8, rounded)

    seat = [
        ("M", (-80, -64, 132)), ("Q", (0, -76, 129), (80, -64, 132)),
        ("Q", (88, -61, 132), (87, -49, 132)), ("L", (74, 57, 126)),
        ("Q", (0, 73, 118), (-74, 57, 126)), ("L", (-87, -49, 132)),
        ("Q", (-88, -61, 132), (-80, -64, 132)), ("Z",),
    ]
    render([(op, *((x, y, z - 10) for x, y, z in points)) for op, *points in seat],
           "#a93e35", stroke, 3.6)
    render(seat, "#ff744a", stroke, 3.5)
    render(seat, "url(#red-dots)")
    render([("M", (-79, -60, 133)), ("Q", (0, -70, 132), (80, -60, 133)),
            ("M", (-70, 55, 128)), ("Q", (0, 69, 120), (70, 55, 128))],
           "none", "#ffb278", 2.3)
    for offset in (0, 9, 17):
        render([("M", (-66, -34 + offset, 132)),
                ("Q", (-25, -46 + offset, 126), (27, -34 + offset, 124)),
                ("T", (73, -31 + offset, 131))], "none", "#bf4e38", 1.25,
               'opacity=".72"')

    backrest = [
        ("M", (-82, 78, 224)), ("Q", (-57, 63, 236), (0, 64, 231)),
        ("Q", (55, 63, 236), (82, 78, 224)), ("L", (78, 86, 174)),
        ("Q", (3, 98, 184), (-78, 86, 174)), ("Z",),
    ]
    render(backrest, "#ff7750", stroke, 4.2)
    render(backrest, "url(#red-dots)")
    render([("M", (-81, 78, 224)), ("Q", (-55, 63, 236), (0, 64, 231)),
            ("Q", (55, 63, 236), (81, 78, 224))], "none", "#ffd396", 3)
    render([("M", (-77, 86, 177)), ("Q", (1, 98, 187), (76, 86, 177))],
           "none", "#c54b37", 3)
    for offset in (0, 7, 13):
        render([("M", (-71, 78, 211 - offset)),
                ("Q", (-26, 64, 220 - offset), (18, 77, 211 - offset)),
                ("T", (68, 79, 215 - offset))], "none", "#ca4e35", 1.25,
               'opacity=".66"')
    for x in (-66, 66):
        cx, cy = project((x, 86, 188))
        ellipse(cx, cy, 3.1, 3.1, "#502a3a")
        ellipse(cx - .6, cy - .8, 1.1, 1.1, "#ffd2a2")


def build():
    captions = ("Before you decide, ask who’s missing.", "Give the people affected a real say.")
    swift = ROOT / "src" / "type.swift"
    outlines = check_output(["swift", str(swift), *captions], text=True).splitlines()
    emit(f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}" height="{PAGE_H}" viewBox="0 0 {PAGE_W} {PAGE_H}" role="img" aria-labelledby="title description">
    <title id="title">Make Room</title>
    <desc id="description">An empty orange chair has been pulled up to a round table where four people are talking. {escape(' '.join(captions))}</desc>
    <defs>
      <clipPath id="scene"><rect width="{ART_W}" height="{ART_H}"/></clipPath>
      <pattern id="floor-dots" width="6" height="6" patternUnits="userSpaceOnUse">
        <path d="M1 1h.8v.8h-.8zM4 4h.8v.8h-.8z" fill="#171b43" opacity=".5"/>
      </pattern>
      <pattern id="table-dots" width="7" height="7" patternUnits="userSpaceOnUse">
        <path d="M1 1h1v1h-1zM4.5 4.5h.7v.7h-.7z" fill="#a46f58" opacity=".32"/>
      </pattern>
      <pattern id="blue-dots" width="5" height="5" patternUnits="userSpaceOnUse">
        <path d="M0 0h1v1h-1zM2.5 2.5h1v1h-1z" fill="#20214a" opacity=".34"/>
      </pattern>
      <pattern id="light-dots" width="5" height="5" patternUnits="userSpaceOnUse">
        <path d="M0 0h1v1h-1zM2.5 2.5h1v1h-1z" fill="#dfd6ef" opacity=".37"/>
      </pattern>
      <pattern id="red-dots" width="4.8" height="4.8" patternUnits="userSpaceOnUse">
        <path d="M1 1h.8v.8h-.8zM3.4 3.4h.8v.8h-.8z" fill="#8b2831" opacity=".42"/>
      </pattern>
      <pattern id="amber-dots" width="4" height="4" patternUnits="userSpaceOnUse">
        <path d="M0 0h1.3v1.3H0zM2 2h1.3v1.3H2z" fill="#ffbd7f" opacity=".37"/>
      </pattern>
      <pattern id="shadow-hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(-24)">
        <path d="M0 0V5" stroke="#858dbd" stroke-width=".9" opacity=".40"/>
      </pattern>
      <pattern id="edge-hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(19)">
        <path d="M0 0V4" stroke="#652d42" stroke-width="1.1" opacity=".48"/>
      </pattern>
    </defs>
    <rect width="{PAGE_W}" height="{PAGE_H}" fill="{PAPER}"/>
    """)
    grain(PAGE_W, PAGE_H, 19900, 14, "#784e4d", .23)
    emit('<g transform="translate(51.5 56) scale(.986 1.04)" aria-label="Make Room">')
    draw_heading()
    emit("</g>")
    emit('<g transform="translate(52 224)" clip-path="url(#scene)">')
    draw_floor()
    draw_support()
    draw_invitation()
    draw_left_chair()
    draw_right_chair()
    draw_back_left()
    draw_back_right()
    draw_table()
    draw_paper()
    draw_mug(385, 338, "#747bb6", "#c5c3dc")
    draw_mug(568, 368, "#bd7965", "#efb797")
    draw_mug(289, 413, "#bd7965", "#efb797")
    draw_mug(721, 403, "#747bb6", "#c5c3dc")
    draw_mug(493, 514, "#ef9773", "#f9c999")
    draw_back_arms()
    draw_left_person()
    draw_right_person()
    draw_open_chair()
    grain(ART_W, ART_H, 15600, 29, "#f5e2c5", .20)
    grain(ART_W, ART_H, 8400, 9, "#18152b", .25)
    emit("</g>")

    emit('<path d="M56 1195V1309" stroke="#d85137" stroke-width="8"/>')
    for baseline, caption, outline in zip((1236, 1292), captions, outlines):
        path(outline, INK, extra=f'transform="translate(84 {baseline})" aria-label="{escape(caption)}"')
    emit("</svg>")

    target = ROOT / "output" / "make-room.svg"
    target.write_text("\n".join(parts) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
