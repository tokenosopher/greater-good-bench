// Return to Source — a miniature animated airmail poster.
// Coordinates are in poster points, with the origin at the top left.
#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>
#import <CoreText/CoreText.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#define W 1080
#define H 810
typedef CGPoint P;
typedef struct {double r,g,b;} Color;
static const Color navy={.072,.153,.185}, blue={.148,.291,.370}, mist={.69,.805,.805}, cream={.993,.942,.828}, red={.806,.227,.155};
static CGContextRef g;
static CGImageRef page, backdrop, grain;
static P p(double x,double y){return CGPointMake(x,y);}
static void fill(Color c,double a){CGContextSetRGBFillColor(g,c.r,c.g,c.b,a);}
static void stroke(Color c,double a){CGContextSetRGBStrokeColor(g,c.r,c.g,c.b,a);}
static void rect(double x,double y,double w,double h,Color c,double a){fill(c,a);CGContextFillRect(g,CGRectMake(x,y,w,h));}
static void circle(double x,double y,double r,Color c,double a){fill(c,a);CGContextFillEllipseInRect(g,CGRectMake(x-r,y-r,2*r,2*r));}
static void move(double x,double y){CGContextMoveToPoint(g,x,y);}
static void line(double x,double y){CGContextAddLineToPoint(g,x,y);}
static void curve(double x,double y,double u,double v,double e,double f){CGContextAddCurveToPoint(g,x,y,u,v,e,f);}
static void pen(Color c,double a,double w){stroke(c,a);CGContextSetLineWidth(g,w);CGContextStrokePath(g);}
static void seg(double x,double y,double u,double v,Color c,double a,double w){move(x,y);line(u,v);pen(c,a,w);}
static void poly(const P *v,int n,Color c,double a){CGContextBeginPath(g);CGContextAddLines(g,v,n);CGContextClosePath(g);fill(c,a);CGContextFillPath(g);}
static void img(CGImageRef im,double x,double y,double w,double h){CGContextSaveGState(g);CGContextTranslateCTM(g,x,y+h);CGContextScaleCTM(g,1,-1);CGContextDrawImage(g,CGRectMake(0,0,w,h),im);CGContextRestoreGState(g);}
static CGContextRef canvas(int w,int h,void *data){CGColorSpaceRef cs=CGColorSpaceCreateDeviceRGB();CGContextRef c=CGBitmapContextCreate(data,w,h,8,w*4,cs,kCGBitmapByteOrder32Little|kCGImageAlphaPremultipliedFirst);CGColorSpaceRelease(cs);CGContextTranslateCTM(c,0,h);CGContextScaleCTM(c,1,-1);return c;}
static void type(NSString *s,NSString *font,double size,double track,double x,double y,Color c,double a){
    CTFontRef f=CTFontCreateWithName((__bridge CFStringRef)font,size,NULL);
    NSDictionary *attr=@{(__bridge NSString*)kCTFontAttributeName:(__bridge id)f,(__bridge NSString*)kCTForegroundColorFromContextAttributeName:@YES,(__bridge NSString*)kCTKernAttributeName:@(track)};
    NSAttributedString *as=[[NSAttributedString alloc]initWithString:s attributes:attr];
    CTLineRef l=CTLineCreateWithAttributedString((__bridge CFAttributedStringRef)as);
    CGContextSaveGState(g);CGContextTranslateCTM(g,x,y);CGContextScaleCTM(g,1,-1);CGContextSetTextMatrix(g,CGAffineTransformIdentity);CGContextSetTextPosition(g,0,0);fill(c,a);CTLineDraw(l,g);CGContextRestoreGState(g);CFRelease(l);CFRelease(f);
}
static uint32_t state=82519;
static double rand01(void){state=1664525*state+1013904223;return state/4294967296.0;}
static double ease(double a,double b,double t){double u=fmax(0,fmin(1,(t-a)/(b-a)));return u*u*(3-2*u);}
static double mix(double a,double b,double u){return a+(b-a)*u;}
static P lerp(P a,P b,double u){return p(mix(a.x,b.x,u),mix(a.y,b.y,u));}
static void globe(double x,double y,double r){
    CGContextSaveGState(g);CGContextTranslateCTM(g,x,y);stroke(navy,1);CGContextSetLineWidth(g,1.9);
    for(int i=0;i<2;i++){double v=i?.46:1;CGContextStrokeEllipseInRect(g,CGRectMake(-r*v,-r,r*2*v,2*r));}
    for(int i=-1;i<=1;i++){double dy=i*r*.46,dx=sqrt(r*r-dy*dy);seg(-dx,dy,dx,dy,navy,1,1.5);}
    for(int i=0;i<3;i++){seg(-r-19+i*5,-7+i*6,-r-3,-7+i*6,navy,1,2);seg(r+3,-7+i*6,r+19-i*5,-7+i*6,navy,1,2);}
    CGContextRestoreGState(g);
}
static void landscape(void){
    // A river crossing, engraved in two inks.
    const double x=22,y=174,w=356,h=152;
    CGContextSaveGState(g);CGContextClipToRect(g,CGRectMake(x,y,w,h));CGContextTranslateCTM(g,x,y);
    rect(0,0,w,h,mist,1);
    for(int j=0;j<26;j++)for(int i=0;i<61;i++)circle(i*6.3+(j%2)*3.1,j*5.3,1.1*(1-j/32.),blue,.53);
    circle(286,38,24,cream,1);
    P far[]={p(-5,88),p(30,74),p(55,76),p(89,54),p(132,81),p(178,71),p(204,77),p(241,64),p(287,77),p(324,61),p(363,70),p(363,104),p(-5,104)};poly(far,13,blue,.53);
    rect(0,99,w,60,cream,1);for(int i=0;i<130;i++){double yy=101+rand01()*50,xx=rand01()*360;seg(xx,yy,xx+3+rand01()*25,yy,blue,.70,.9);}
    for(int k=0;k<2;k++){
        double bx=k?264:100;P tower[]={p(bx-7,118),p(bx-4,34),p(bx-5,28),p(bx+5,28),p(bx+4,34),p(bx+8,118)};poly(tower,6,navy,1);
        rect(bx-6,33,12,3,cream,1);rect(bx-10,115,20,7,navy,1);
    }
    for(int k=0;k<3;k++){
        double a=k==0?-63:k==1?100:264,b=k==0?100:k==1?264:427;
        move(a,36);CGContextAddQuadCurveToPoint(g,(a+b)/2,132,b,36);pen(navy,1,2.8);
        for(int j=1;j<15;j++){double u=j/15.,xx=mix(a,b,u),yy=36+192*u*(1-u);seg(xx,yy,xx,93,navy,1,1.3);}
    }
    rect(-2,90,360,8,navy,1);seg(0,92,357,92,cream,.7,.9);CGContextRestoreGState(g);
}
static void makePage(void){
    // Build at double resolution so the type stays crisp throughout the fold.
    CGContextRef old=g;g=canvas(800,952,NULL);CGContextScaleCTM(g,2,2);
    rect(0,0,400,476,cream,1);
    seg(20,20,380,20,navy,1,2);
    type(@"The Daily Post",@"HoeflerText-Black",43,-1.9,21,64,navy,1);
    seg(20,76,380,76,navy,1,3);seg(20,81,380,81,navy,1,1);
    type(@"BRIDGE CLOSED",@"DINCondensed-Bold",56,-.6,21,140,navy,1);
    type(@"One day of repairs on the river crossing",@"Baskerville-Italic",19,0,22,163,navy,1);
    landscape();
    type(@"FRIDAY, JUNE 12, 1998",@"Menlo-Bold",16,.15,22,355,navy,1);
    seg(22,369,378,369,navy,1,1.3);
    for(int k=0;k<3;k++){
        for(int j=0;j<16;j++){
            double xx=22+k*122,yy=382+4.5*j,end=xx+110-(j==15?rand01()*45:0);
            while(xx<end-2){double len=fmin(end-xx,4+rand01()*15);rect(xx,yy,len,1.05+rand01()*.8,navy,.76);xx+=len+1.6;}
        }
    }
    for(int i=0;i<4500;i++)circle(rand01()*400,rand01()*476,.22+rand01()*.6,blue,.12);
    page=CGBitmapContextCreateImage(g);CGContextRelease(g);g=old;
}
static void cloud(double x,double y,double s){
    CGContextSaveGState(g);CGContextTranslateCTM(g,x,y);CGContextScaleCTM(g,s,s);move(-140,0);
    curve(-125,-4,-121,-20,-103,-15);curve(-95,-42,-59,-43,-51,-26);curve(-34,-76,20,-68,37,-37);curve(64,-43,80,-26,82,-16);curve(104,-18,120,-3,153,0);
    CGContextClosePath(g);fill(cream,.46);CGContextFillPath(g);CGContextRestoreGState(g);
}
static void makeBackdrop(void){
    CGContextRef old=g;g=canvas(W,H,NULL);rect(0,0,W,H,cream,1);
    rect(0,96,W,600,mist,1);
    // Fading screen of dots around the sun.
    for(int j=-44;j<=44;j++)for(int i=-44;i<=44;i++){double xx=i*5.7+(j%2)*2.85,yy=j*5.7,d=hypot(xx,yy);if(d<230)circle(804+xx,371+yy,1.2+.85*(1-d/230),cream,.64);}
    cloud(710,240,.9);cloud(988,560,.94);cloud(287,611,.65);cloud(1071,174,.5);
    seg(0,96,W,96,navy,1,2);seg(0,696,W,696,navy,1,2);
    globe(83,49,19);
    type(@"RETURN TO SOURCE",@"HelveticaNeue-Bold",23,1.7,140,58,navy,1);
    // Bilingual airmail lozenge.
    rect(818,30,216,35,navy,1);
    type(@"AIR MAIL  /  PAR AVION",@"DINCondensed-Bold",19,1.2,836,54,cream,1);
    for(int i=-1;i<35;i++){double x=i*48;P v[]={p(x,799),p(x+21,799),p(x+10,810),p(x-11,810)};poly(v,4,i%2?red:blue,1);}
    // Press wear, pulp fibres and ink flecks, registered to the stock.
    for(int i=0;i<27500;i++){double x=rand01()*W,y=rand01()*H,r=.15+rand01()*.9;circle(x,y,r,i%3?blue:cream,.08+rand01()*.12);}
    backdrop=CGBitmapContextCreateImage(g);CGContextRelease(g);g=old;
}
static void makeGrain(void){
    uint8_t *buf=malloc(W*H*4);for(int k=0;k<W*H;k++){double n=(rand01()+rand01()-1);uint8_t a=(int)(fabs(n)*28);
        buf[4*k+3]=a;for(int j=0;j<3;j++)buf[4*k+j]=n<0?0:a;}
    CGContextRef c=canvas(W,H,buf);grain=CGBitmapContextCreateImage(c);CGContextRelease(c);free(buf);
}
static void pathHead(double t){
    // Hand-inked loop of the aeroplane's flight, progressively laid down.
    const P knots[][4]={
        {{-25,582},{72,550},{161,610},{261,599}},
        {{261,599},{383,589},{485,457},{429,428}},
        {{429,428},{378,401},{358,493},{426,516}},
        {{426,516},{510,550},{575,463},{678,430}}
    };
    double travel= fmin(1,.62+t*.19)*4, dist=0;
    for(int k=0;k<4;k++){P prev=knots[k][0];for(int j=1;j<=190;j++){
        double u=j/190.,v=1-u;if(k+u>travel)return;
        P q=p(0,0);for(int h=0;h<4;h++){double z=h==0?v*v*v:h==1?3*v*v*u:h==2?3*v*u*u:u*u*u;q.x+=z*knots[k][h].x;q.y+=z*knots[k][h].y;}
        double d=hypot(q.x-prev.x,q.y-prev.y);
        if(fmod(dist,16)<8)seg(prev.x,prev.y,q.x,q.y,blue,.65,2.4);
        dist+=d;prev=q;
    }}
}
static void triangle(P *src,P *dst,double shade){
    double sx1=src[1].x-src[0].x,sy1=src[1].y-src[0].y,sx2=src[2].x-src[0].x,sy2=src[2].y-src[0].y;
    double dx1=dst[1].x-dst[0].x,dy1=dst[1].y-dst[0].y,dx2=dst[2].x-dst[0].x,dy2=dst[2].y-dst[0].y,det=sx1*sy2-sx2*sy1;
    double a=(dx1*sy2-dx2*sy1)/det,b=(dy1*sy2-dy2*sy1)/det,c=(dx2*sx1-dx1*sx2)/det,d=(dy2*sx1-dy1*sx2)/det;
    if(fabs(a*d-b*c)<.0001)return;
    CGContextSaveGState(g);
    CGContextBeginPath(g);CGContextAddLines(g,dst,3);CGContextClosePath(g);CGContextClip(g);
    CGContextConcatCTM(g,CGAffineTransformMake(a,b,c,d,dst[0].x-a*src[0].x-c*src[0].y,dst[0].y-b*src[0].x-d*src[0].y));
    img(page,0,0,400,476);if(shade>0)rect(-2,-2,404,480,blue,shade);CGContextRestoreGState(g);
}
static void paper(double t){
    double u=ease(2.95,4.77,t);
    const P source[]={{200,0},{0,0},{0,476},{141,476},{200,476},{253,476},{400,476},{400,0}};
    const P plane[]={{294,-113},{-180,-97},{-261,-78},{-124,8},{-128,82},{-99,26},{-168,152},{-75,111}};
    double entry=ease(-.25,1.52,t),lift=sin(M_PI*u);
    double x=mix(681,740,entry)+mix(0,37,u), y=363+77*(1-entry)+sin(t*3)*4*(1-u)+21*u-30*lift;
    double angle=(-.045+.10*sin(t*2.4))*(1-u)-.073*u;
    CGContextSaveGState(g);CGContextTranslateCTM(g,x,y);CGContextRotateCTM(g,angle);
    P v[8];for(int i=0;i<8;i++){
        P flat=p((source[i].x-200)*1.025,(source[i].y-238)*1.025);
        v[i]=lerp(plane[i],flat,u);v[i].y+=lift*(i==2||i==6?-61:i==4?48:0);
    }
    P shadow[8];for(int i=0;i<8;i++)shadow[i]=p(v[i].x+7,v[i].y+10+3*(1-u));poly(shadow,8,navy,.16);
    poly(v,8,cream,1);
    int order[]={1,2,3,4,5,6};double shades[]={.02,.09,.52,.73,.025,.02};
    for(int j=0;j<6;j++){int k=order[j];P src[]={source[0],source[k],source[k+1]},dst[]={v[0],v[k],v[k+1]};
        triangle(src,dst,shades[j]*mix(1,.095,u));
    }
    for(int k=2;k<7;k++)seg(v[0].x,v[0].y,v[k].x,v[k].y,blue,mix(.55,.11,u),.9);
    // A grease-pencil oval picks the publication date out of the page.
    double mark=ease(5.10,6.26,t);
    if(mark>0){CGContextScaleCTM(g,1.025,1.025);CGContextTranslateCTM(g,-200,-238);
        int n=ceil(mark*135);for(int i=0;i<=n;i++){
            double z=i/135.,a=-1.10+z*6.66,rx=132+sin(a*3)*1.35;
            double xx=142+rx*cos(a),yy=348+19*sin(a)-.017*(xx-142)+.7*cos(a*2);
            if(!i)move(xx,yy);else line(xx,yy);}
        CGContextSetLineCap(g,kCGLineCapRound);pen(red,.94,3.8);
    }
    CGContextRestoreGState(g);
}
static void label(NSString *s,double y,double a){
    rect(53,y-11,21,4,red,a);type(s,@"Menlo-Bold",15,.9,87,y,navy,a);
}
static void frame(double t){
    img(backdrop,0,0,W,H);pathHead(t);
    double out=ease(2.73,3.18,t),in=ease(3.29,3.84,t);
    if(out<1){
        label(@"PASSED ALONG TODAY",215-9*out,1-out);
        type(@"Bridge",@"HelveticaNeue-CondensedBlack",116,-3.8,47,330-9*out,navy,1-out);
        type(@"closed!",@"Baskerville-BoldItalic",113,-4.8,49,424-9*out,navy,1-out);
    }
    if(in>0){
        label(@"BACK AT THE SOURCE",215+10*(1-in),in);
        type(@"Closed",@"HelveticaNeue-CondensedBlack",116,-3.8,47,330+10*(1-in),navy,in);
        type(@"when?",@"Baskerville-BoldItalic",117,-4.3,49,424+10*(1-in),navy,in);
    }
    paper(t);
    double transition=ease(3.02,3.54,t);
    circle(70,747,19,red,1);
    // Simple postal arrow becomes a magnifier.
    if(transition<1){seg(60,747,79,747,cream,1-transition,2.8);move(72,740);line(79,747);line(72,754);pen(cream,1-transition,2.8);}
    if(transition>0){stroke(cream,transition);CGContextSetLineWidth(g,2.6);CGContextStrokeEllipseInRect(g,CGRectMake(61,737,13,13));seg(72,748,80,756,cream,transition,3);}
    double a1=1-ease(2.80,3.10,t),a2=ease(3.33,3.70,t);
    if(a1>0)type(@"Would you pass it on?",@"Baskerville-Italic",33,-.3,108,757,navy,a1);
    if(a2>0)type(@"Find the original. Check the date before you share.",@"Baskerville-SemiBold",30,-.45,108,757,navy,a2);
    for(int j=0;j<3;j++){move(920,735+j*10);curve(940,722+j*10,953,750+j*10,974,736+j*10);curve(994,722+j*10,1006,748+j*10,1028,734+j*10);pen(blue,.68,1.8);}
    img(grain,0,0,W,H);
}
int main(int argc,char **argv){@autoreleasepool{
    makePage();makeBackdrop();makeGrain();
    uint8_t *data=malloc(W*H*4);g=canvas(W,H,data);CGContextSetInterpolationQuality(g,kCGInterpolationHigh);
    int first=argc>1?atoi(argv[1]):0,last=argc>1?first+1:228;
    for(int i=first;i<last;i++){@autoreleasepool{frame(i/24.);CGContextFlush(g);fwrite(data,1,W*H*4,stdout);}}
    CGContextRelease(g);free(data);CGImageRelease(page);CGImageRelease(backdrop);CGImageRelease(grain);
}return 0;}
