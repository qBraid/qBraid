gate u0(gamma) q { u3(0,0,0) q; }
gate u(theta,phi,lambda) q { u3(theta,phi,lambda) q; }
gate sxdg a { s a; h a; s a; }
gate csx a, b { ctrl @ sx a, b; }
gate cu1 (lambda) a, b {
  u3(0,0,lambda/2) a;
  cx a,b;
  u3(0,0,-lambda/2) b;
  cx a,b;
  u3(0,0,lambda/2) b; 
}
gate cu3(theta,phi,lambda) c, t {
  u3(0,0,(lambda+phi)/2) c;
  u3(0,0,(lambda-phi)/2) t;
  cx c,t;
  u3(-theta/2,0,-(phi+lambda)/2) t;
  cx c,t;
  u3(theta/2,phi,0) t;
}
gate rzz(theta) a, b {
  cx a,b;
  u3(0,0,theta) b;
  cx a,b;
}
gate rccx a, b, c {
  u2(0,pi) c;
  u3(0,0,pi/4) c;
  cx b, c;
  u3(0,0,-pi/4) c;
  cx a, c;
  u3(0,0,pi/4) c;
  cx b, c;
  u3(0,0,-pi/4) c;
  u2(0,pi) c;
}
gate rc3x a, b, c, d {
  u2(0,pi) d;
  u3(0,0,pi/4) d;
  cx c,d;
  u3(0,0,-pi/4) d;
  u2(0,pi) d;
  cx a,d;
  u3(0,0,pi/4) d;
  cx b,d;
  u3(0,0,-pi/4) d;
  cx a,d;
  u3(0,0,pi/4) d;
  cx b,d;
  u3(0,0,-pi/4) d;
  u2(0,pi) d;
  u3(0,0,pi/4) d;
  cx c,d;
  u3(0,0,-pi/4) d;
  u2(0,pi) d;
}
gate c3x a, b, c, d {
  ctrl (3) @ x a, b, c, d;   
}
gate c3sqrtx a, b, c, d {
  ctrl (3) @ sx a, b, c, d;
}
gate c4x a, b, c, d, e {
  ctrl (4) @ x a, b, c, d, e; 
}