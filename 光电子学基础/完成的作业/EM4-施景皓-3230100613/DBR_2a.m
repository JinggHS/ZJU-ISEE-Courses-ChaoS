%  EM4 Homework Q2(a)
%  Wavelength-angle diagrams for a 10-layer DBR
%  Center wavelength = 500 nm
%  TM and TE are plotted together for each refractive-index-ratio case
%  No defect layer in this code

function DBR_2a
clc; clear; close all;

% wavelength and angle ranges
y = 200:5:800;      % wavelength (nm)
theta = 0:1:90;     % incident angle (degree)


% Case 1: n1/n2 = 2
% Example: n1 = 3, n2 = 1.5

n2 = 1.5;
n1 = 3.0;
lambda0 = 500;   % center wavelength (nm)
plot_case(y, theta, n1, n2, lambda0, 'n1/n2 = 2  (n1 = 3, n2 = 1.5)');

% Case 2: n1/n2 = 4
% Example: n1 = 6, n2 = 1.5

n2 = 1.5;
n1 = 6.0;
lambda0 = 500;   % center wavelength (nm)
plot_case(y, theta, n1, n2, lambda0, 'n1/n2 = 4  (n1 = 6, n2 = 1.5)');

end


function plot_case(y, theta, n1, n2, lambda0, fig_title_text)

res_TM = zeros(length(theta), length(y));
res_TE = zeros(length(theta), length(y));

for m = 1:length(theta)
    fprintf('%s, angle = %d deg\n', fig_title_text, theta(m));

    % TM
    res_TM(m, :) = G_Ref(y, theta(m), 1, n1, n2, lambda0);

    % TE
    res_TE(m, :) = G_Ref(y, theta(m), 0, n1, n2, lambda0);
end

figure;
subplot(1,2,1)
pcolor(theta, y, abs(res_TM.').^2);
shading interp
xlabel('Angle (degree)');
ylabel('Wavelength (nm)');
title(['Generalized Reflectance (TM), ' fig_title_text]);
colorbar

subplot(1,2,2)
pcolor(theta, y, abs(res_TE.').^2);
shading interp
xlabel('Angle (degree)');
ylabel('Wavelength (nm)');
title(['Generalized Reflectance (TE), ' fig_title_text]);
colorbar

end



function res = G_Ref(y, theta, flag, n1, n2, lambda0)

eps0 = 1/(4*pi*9*10^9);   % permittivity in free space
mur0 = 4*pi*10^(-7);      % permeability in free space

x = y * 1e-9;             % wavelength in meter
omega = 2*pi*3e8 ./ x;    % angular frequency

% total layer number including two air layers
N = 12;

% quarter-wave thickness design
d1 = (lambda0/4) / n1;    % nm
d2 = (lambda0/4) / n2;    % nm

% 10-layer DBR:
% air | n1 | n2 | n1 | n2 | n1 | n2 | n1 | n2 | n1 | n2 | air
thick = [d1, d2, d1, d2, d1, d2, d1, d2, d1, d2, 0];
thick = thick * 1e-9;     % convert to meter

AIR  = ones(length(y),1);
Die1 = (n1)^2 * ones(length(y),1);
Die2 = (n2)^2 * ones(length(y),1);

res = zeros(1, length(y));

for fre = 1:length(x)

    epr_arr = [AIR(fre), Die1(fre), Die2(fre), Die1(fre), Die2(fre), ...
               Die1(fre), Die2(fre), Die1(fre), Die2(fre), Die1(fre), ...
               Die2(fre), AIR(fre)];

    % wave number in each layer
    k0 = sqrt(omega(fre)^2 * eps0 * mur0);
    k_arr1 = sqrt(epr_arr) * k0;

    % tangential wave number
    % incident medium is air
    kx = k0 * sin(theta*pi/180);

    % vertical wave number kz
    k_arr = sqrt(k_arr1.^2 - kx^2);

    % reflection coefficient for each interface
    ref = zeros(1, N-1);
    for m = 1:N-1
        if flag == 1
            % TM polarization
            ref(m) = (k_arr(m)/epr_arr(m) - k_arr(m+1)/epr_arr(m+1)) / ...
                     (k_arr(m)/epr_arr(m) + k_arr(m+1)/epr_arr(m+1));
        else
            % TE polarization
            ref(m) = (k_arr(m) - k_arr(m+1)) / ...
                     (k_arr(m) + k_arr(m+1));
        end
    end

    % recursive generalized reflection coefficient
    ref_x = 0;
    for m = 1:N-1
        ref_x = (ref(N-m) + ref_x * exp(2*(-1i)*k_arr(N+1-m)*thick(N-m))) / ...
                (1 + ref(N-m)*ref_x*exp(2*(-1i)*k_arr(N+1-m)*thick(N-m)));
    end

    res(fre) = ref_x;
end

end

