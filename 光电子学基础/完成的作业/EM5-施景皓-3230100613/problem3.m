clc; clear; close all;

%% =========================================================
% Air-Dielectric-Air slab waveguide
% Two figures:
%   Fig.1: k_rho constraint region + light lines
%   Fig.2: dispersion relation from poles of generalized reflection coefficient
%
% Structure:
%   air | dielectric | air
%   n_core = 4
%   d = 125 nm
%   wavelength: 200 nm ~ 10000 nm
%% =========================================================

%% constants
c0 = 299792458;
eps0 = 8.854187817e-12;
mu0 = 4*pi*1e-7;

%% structure
n_clad = 1.0;
n_core = 4.0;
d = 125e-9;

%% wavelength range
lambda_nm = linspace(200, 10000, 500);
lambda_m  = lambda_nm * 1e-9;
Nlam = numel(lambda_m);

%% scan beta = k_rho
Nbeta = 5000;
prom_TE = 30;
prom_TM = 30;

beta_TE = [];
omega_TE = [];
beta_TM = [];
omega_TM = [];

fprintf('Scanning guided modes...\n');

for ii = 1:Nlam
    lambda = lambda_m(ii);
    omega = 2*pi*c0/lambda;
    k0 = omega/c0;

    % guided-mode window
    beta_min = n_clad*k0*(1+1e-6);
    beta_max = n_core*k0*(1-1e-6);

    if beta_min >= beta_max
        continue;
    end

    beta = linspace(beta_min, beta_max, Nbeta);

    % vertical wavevectors
    alpha = sqrt(beta.^2 - (n_clad*k0).^2);      % evanescent in air
    h     = sqrt((n_core*k0).^2 - beta.^2);      % oscillatory in slab

    kz1 = 1i*alpha;
    kz2 = h;
    kz3 = 1i*alpha;

    eps1 = n_clad^2;
    eps2 = n_core^2;
    eps3 = n_clad^2;

    % Fresnel coeffs
    % TE
    r12_TE = (kz1 - kz2) ./ (kz1 + kz2);
    r23_TE = (kz2 - kz3) ./ (kz2 + kz3);

    % TM
    r12_TM = (eps2*kz1 - eps1*kz2) ./ (eps2*kz1 + eps1*kz2);
    r23_TM = (eps3*kz2 - eps2*kz3) ./ (eps3*kz2 + eps2*kz3);

    % generalized reflection coefficient denominator
    denom_TE = 1 + r12_TE .* r23_TE .* exp(2i*kz2*d);
    denom_TM = 1 + r12_TM .* r23_TM .* exp(2i*kz2*d);

    inv_TE = 1 ./ abs(denom_TE);
    inv_TM = 1 ./ abs(denom_TM);

    % find all poles/peaks
    [~, locsTE] = findpeaks(inv_TE, 'MinPeakProminence', prom_TE);
    [~, locsTM] = findpeaks(inv_TM, 'MinPeakProminence', prom_TM);

    if ~isempty(locsTE)
        beta_TE  = [beta_TE, beta(locsTE)];
        omega_TE = [omega_TE, omega*ones(size(locsTE))];
    end

    if ~isempty(locsTM)
        beta_TM  = [beta_TM, beta(locsTM)];
        omega_TM = [omega_TM, omega*ones(size(locsTM))];
    end

    if mod(ii,50)==0
        fprintf('  %d / %d done\n', ii, Nlam);
    end
end

fprintf('Done.\n');

%% =========================================================
% Figure 1: k_rho constraint region
%% =========================================================
figure('Color','w');
hold on;

omega_plot = linspace(0, max([omega_TE, omega_TM])*1.05, 400);

% light lines: beta = n*omega/c
beta_air  = n_clad * omega_plot / c0;
beta_core = n_core * omega_plot / c0;

% ===== 边界线：全部绿色 =====
plot(beta_air,  omega_plot, '--', 'Color', [0 0.6 0], 'LineWidth', 2, ...
    'DisplayName', 'air light line');

plot(beta_core, omega_plot, '--', 'Color', [0 0.6 0], 'LineWidth', 2, ...
    'DisplayName', 'dielectric light line');


% fill guided-mode region
x_fill = [beta_air, fliplr(beta_core)];
y_fill = [omega_plot, fliplr(omega_plot)];
fill(x_fill, y_fill, [0.85 0.93 1.0], ...
    'FaceAlpha', 0.45, 'EdgeColor', 'none', ...
    'DisplayName', 'guided-mode region');

% representative label
text(mean(beta_air)*1.6, max(omega_plot)*0.75, ...
    'guided modes satisfy:  k_0 < k_\rho < 4k_0', ...
    'FontSize', 12, 'Color', [0 0.2 0.7]);

xlabel('k_\rho (rad/m)');
ylabel('\omega (rad/s)');
title('Constraint relation between k_\rho and \omega');
legend('Location','northwest');
grid on; box on;

xlim([0, max(beta_core)*1.05]);
ylim([0, max(omega_plot)]);

%% =========================================================
% Figure 2: dispersion relation
%% =========================================================
figure('Color','w');
hold on;

% light lines
plot(beta_air,  omega_plot, 'k--', 'LineWidth', 2, 'DisplayName', 'air light line');
plot(beta_core, omega_plot, 'b--', 'LineWidth', 2, 'DisplayName', 'dielectric light line');

% TE/TM modes
if ~isempty(beta_TE)
    scatter(beta_TE, omega_TE, 16, 'r', 'filled', 'DisplayName', 'TE modes');
end
if ~isempty(beta_TM)
    scatter(beta_TM, omega_TM, 16, 'blue', 'filled', 'DisplayName', 'TM modes');
end

xlabel('k_\rho (rad/m)');
ylabel('\omega (rad/s)');
title('Dispersion relation of guided modes');
legend('Location','southeast');
grid on; box on;

xlim([0, max(beta_core)*1.05]);
ylim([0, max(omega_plot)]);

%% =========================================================
% optional: print cutoff wavelengths
%% =========================================================
fprintf('\nApproximate cutoff wavelengths:\n');
for m = 1:8
    lambda_c = 2*d*sqrt(n_core^2 - n_clad^2)/m;
    fprintf('m = %d, lambda_c ~ %.2f nm\n', m, lambda_c*1e9);
end