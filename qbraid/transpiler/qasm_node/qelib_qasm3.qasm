// QASM 3 equivalent definitions of qelib1.inc gates

// idle gate (identity) with length gamma*sqglen
gate u0(gamma) q { u3(0,0,0) q; }
 
// generic single qubit gate
gate u(theta,phi,lambda) q { u3(theta,phi,lambda) q; }


// inverse sqrt(X)
gate sxdg a { s a; h a; s a; }

// controlled-sqrt(X)
gate csx a, b {ctrl @ sx a, b;}

// controlled phase rotation 
gate cu1 (lambda) a, b{  
  
  u3(0,0,lambda/2) a;
  cx a,b;
  u3(0,0,-lambda/2) b;
  cx a,b;
  u3(0,0,lambda/2) b; 
  
}

// controlled-U
gate cu3(theta,phi,lambda) c, t
{
  // implements controlled-U(theta,phi,lambda) with  target t and control c
  u3(0,0,(lambda+phi)/2) c;
  u3(0,0,(lambda-phi)/2) t;
  cx c,t;
  u3(-theta/2,0,-(phi+lambda)/2) t;
  cx c,t;
  u3(theta/2,phi,0) t;
}

// two-qubit XX rotation
// gate rxx(theta) a, b
// {
//   u3(pi/2, theta, 0) a;
//   h b;
//   cx a,b;
//   u1(-theta) b;
//   cx a,b;
//   h b;
//   ******** why type error ********
//   // u2(-pi, pi-theta) b;
// }

// two-qubit ZZ rotation
gate rzz(theta) a,b
{
  cx a,b;
  u3(0,0,theta) b;
  cx a,b;
}

// relative-phase CCX
gate rccx a,b,c
{
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

// relative-phase 3-controlled X gate
gate rc3x a,b,c,d
{
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

// 3-controlled X gate
gate c3x a,b,c,d
{
    ctrl (3) @ x a, b, c, d;   
}

// 3-controlled sqrt(X) gate, this equals the C3X gate 
// where the CU1 rotations are -pi/8 not -pi/4
gate c3sqrtx a,b,c,d 
{
    ctrl (3) @ sx a, b, c, d;
}

// 4-controlled X gate 
gate c4x a,b,c,d,e
{
    ctrl (4) @ x a, b, c, d, e; 
}

 