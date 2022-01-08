param n;

set N := 1..n;

param Dc{N};
param usable{N};

param Cx{N};
param Cy{N};

param distance{i in N, j in N} := sqrt((Cx[j]-Cx[i])**2 + (Cy[j]-Cy[i])**2);

param range;

param Vc default 0.1;
param Fc default 100;
param capacity default 10;

var y{N} binary;

minimize cost:
	sum{i in N} Dc[i]*y[i];

s.t. coverage {i in N}:
	sum{j in N: distance[i,j]<=range} y[j] >= 1;
	
s.t. cannotUseNonUsablePoints {i in N: usable[i]=0}:
	y[i]=0;
	
s.t. depotIsAlwaysBuilt:
        y[1]=1;
	
		
	
