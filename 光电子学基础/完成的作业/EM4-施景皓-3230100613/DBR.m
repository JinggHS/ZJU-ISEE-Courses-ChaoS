%  omega-angle diagram for distributed bragg reflector (DBR)
%  non-magnetic materials are assumed
%  The code was written by Wei Sha from Zhejiang University
%  Email: weisha@zju.edu.cn

function DBR
clc;clear

%  omega-angle diagram

y=400:5:1000; % wavelength  ****
theta=0:1:90; % incident angle  ****
flag=1;       % polarization flag=1 TM, flag=0 TE ****

index=0;
for m=1:1:length(theta) % angle
    index=index+1
    [res]=G_Ref(y,theta(m),flag);
    res_1(index,:)=res;
end

figure
pcolor(theta,y,abs(res_1.').^2)
shading interp
ylabel('Wavelength (nm)')
xlabel('Angle')
title('Generalized Reflectance')
colorbar

% compute generalized reflection coef for DBR
% y 波长 wavelength 
% theta 入射角 incident angle
% flag=1 TM, flag=0 TE
function [res]=G_Ref(y,theta,flag)

%clc;clear
eps0=1/(4*pi*9*10.^9);      %  自由空间介电常数 (permittivity in free space)     
mur0=4*pi*10.^(-7);         %  自由空间磁导率 (permeability) 


%y=400:5:1000;               %  波长 (wavelength range nm)
x=y*10^(-9);                 %  nanometer

omega=2*pi*3*10^8./(x);     %  角频率 (angular frequency)

%  层数(包括空气) layer number (including air layers) 
N=12;  %  ****

%  波从前到后入射，最后一层厚度0，第一层不需要输入***
%  wave propagates from front to back media; thickness of last-layer media is zero; 
%  no input is needed for the first air layer

thick=[50,100,50,100,50,100,50,100,50,100,0]; % ****
thick=thick*10^(-9);

%  入射角 incident angle (vertical 0)
% theta=0;

AIR=ones(length(y),1);         % 空气相对介电常数 relative permittivity of air 
Die1=3^2*ones(length(y),1);    % 介质1相对介电常数 relative permittivity of dielectric 1 ****
Die2=1.5^2*ones(length(y),1);  % 介质2相对介电常数 relative permittivity of dielectric 2 ****

for fre=1:length(x)
    epr_arr=[AIR(fre),Die1(fre),Die2(fre),Die1(fre),Die2(fre),...
             Die1(fre),Die2(fre),Die1(fre),Die2(fre),Die1(fre),Die2(fre),AIR(fre)]; %  波从前到后入射 (from front to back layers)
    
    k_arr1=sqrt(epr_arr)*sqrt(omega(fre)^2*eps0*mur0); % dielectric wave number
    kx=sqrt(omega(fre)^2*eps0*mur0)*sin(theta*pi/180); % tangential wave number
    k_arr=sqrt(k_arr1.^2-kx^2);  %  kz vertical wave number
    
    %  计算每一层的反射系数 (reflection coef for each layer)
    for m=1:N-1
        if (flag==1)
            ref(m)=(k_arr(m)/epr_arr(m)-(k_arr(m+1)/epr_arr(m+1)))/(k_arr(m)/epr_arr(m)+(k_arr(m+1)/epr_arr(m+1)));  % P/TM polarization ***
        else
            ref(m)=(k_arr(m)-k_arr(m+1))/(k_arr(m)+k_arr(m+1));  %  S/TE polarization ***
        end
    end
    
    %  计算广义反射系数 (recursive equation for generalized reflection coef)
    ref_x=0;
    for m=1:N-1
        ref_x=(ref(N-m)+ref_x*exp(2*(-j)*k_arr(N+1-m)*thick(N-m)))/(1+ref(N-m)*ref_x*exp(2*(-j)*k_arr(N+1-m)*thick(N-m)));
    end
    res(fre)=ref_x;
end



