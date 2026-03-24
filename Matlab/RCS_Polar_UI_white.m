function RCS_Polar_UI()
    fprintf('Loading STL...\n');
    TR       = stlread('JetRayComp_new_sweep_alt_2.stl');
    vertices = TR.Points;
    faces    = TR.ConnectivityList;
    c        = physconst('LightSpeed');
    az       = -180:2:180;

    %% Check GPU availability
    useGPU = false;
    try
        gpu = gpuDevice();
        fprintf('GPU Found: %s\n', gpu.Name);
        fprintf('GPU Memory: %.1f GB\n', gpu.TotalMemory/1e9);
        useGPU = true;
    catch
        fprintf('No GPU found - using CPU\n');
    end

    bands = {
        'HF',     20e6;
        'VHF',    100e6;
        'UHF',    300e6;
        'L-band', 1.5e9;
        'S-band', 3e9;
        'C-band', 5.5e9;
        'X-band', 10e9;
        'Ku-band',15e9;
        'K-band', 24e9;
        'Ka-band',35e9;
    };

    colors = [
        0.85, 0.15, 0.15;
        0.90, 0.50, 0.05;
        0.75, 0.65, 0.00;
        0.10, 0.65, 0.20;
        0.00, 0.60, 0.45;
        0.05, 0.45, 0.80;
        0.20, 0.30, 0.85;
        0.60, 0.10, 0.80;
        0.80, 0.10, 0.45;
        0.70, 0.10, 0.10;
    ];

    % ── White-theme palette ──────────────────────────────────────────────
    BG_MAIN   = [0.95 0.96 0.98];   % page background
    BG_PANEL  = [1.00 1.00 1.00];   % panel background
    BG_BTN    = [0.88 0.92 0.98];   % inactive button
    BG_BTNON  = [0.20 0.47 0.78];   % active/selected button
    FC_HDR    = [0.12 0.25 0.55];   % header / title text
    FC_LBL    = [0.25 0.30 0.40];   % secondary labels
    FC_STAT   = [0.20 0.25 0.35];   % stats bar text
    BD_COLOR  = [0.75 0.80 0.90];   % panel borders
    AX_BG     = [0.98 0.98 1.00];   % polar axes background
    AX_GRID   = [0.70 0.75 0.85];   % grid lines
    AX_TICK   = [0.25 0.30 0.45];   % axis tick labels
    % ────────────────────────────────────────────────────────────────────

    %% Pre-compute geometry ONCE
    fprintf('Pre-computing geometry...\n');

    v1_all = vertices(faces(:,1),:);
    v2_all = vertices(faces(:,2),:);
    v3_all = vertices(faces(:,3),:);

    edge1       = v2_all - v1_all;
    edge2       = v3_all - v1_all;
    normals_raw = cross(edge1, edge2, 2);
    areas       = vecnorm(normals_raw, 2, 2) / 2;
    normals     = normals_raw ./ vecnorm(normals_raw, 2, 2);
    centroids   = (v1_all + v2_all + v3_all) / 3;

    fprintf('Geometry done: %d faces\n', size(faces,1));

    %% Transfer to GPU if available
    if useGPU
        normals_g   = gpuArray(single(normals));
        areas_g     = gpuArray(single(areas));
        centroids_g = gpuArray(single(centroids));
        fprintf('Geometry transferred to GPU\n');
    end

    %% Pre-compute all bands
    bandRCS   = cell(size(bands,1),1);
    bandStats = zeros(size(bands,1),4);

    for b = 1:size(bands,1)
        freq   = bands{b,2};
        lambda = c/freq;
        k      = 2*pi/lambda;
        fprintf('Computing %s... ', bands{b,1});
        tic;

        if useGPU
            rcs_az = computeRCS_GPU(az, k, lambda, ...
                                    normals_g, areas_g, centroids_g);
        else
            rcs_az = computeRCS_CPU(az, k, lambda, ...
                                    normals, areas, centroids);
        end

        t = toc;
        fprintf('%.1f seconds\n', t);

        bandRCS{b}     = 10*log10(rcs_az);
        bandStats(b,:) = [bandRCS{b}(az==0), bandRCS{b}(az==90), ...
                          max(bandRCS{b}), min(bandRCS{b})];
        fprintf('  Nose:%.2f Side:%.2f Max:%.2f Min:%.2f dBsm\n', ...
                bandStats(b,:));
    end
    fprintf('All done! Launching UI...\n');

    viewMode   = 'single';
    activeBand = 7;

    %% Main Figure
    fig = uifigure('Name','RCS Polar Analyzer - Blended Wing UAV', ...
                   'Position',[30 30 1380 820], ...
                   'Color', BG_MAIN);

    uilabel(fig, ...
            'Text','BLENDED WING UAV  —  RCS POLAR PATTERN ANALYZER', ...
            'Position',[0 788 1380 28], ...
            'HorizontalAlignment','center', ...
            'FontSize',14,'FontWeight','bold', ...
            'FontColor', FC_HDR);

    %% Left Panel
    leftPanel = uipanel(fig,'Position',[8 8 220 775], ...
                        'BackgroundColor', BG_PANEL, ...
                        'BorderColor',     BD_COLOR, ...
                        'Title','SELECT BAND', ...
                        'ForegroundColor', FC_HDR, ...
                        'FontSize',11);

    uilabel(leftPanel,'Text','VIEW MODE:', ...
            'Position',[10 730 100 18],'FontSize',9, ...
            'FontColor', FC_LBL);

    btnSingle = uibutton(leftPanel,'Text','SINGLE', ...
        'Position',[10 705 90 26], ...
        'BackgroundColor', BG_BTNON, ...
        'FontColor',[1 1 1],'FontSize',10, ...
        'ButtonPushedFcn',@(~,~) setMode('single'));

    btnCompare = uibutton(leftPanel,'Text','COMPARE', ...
        'Position',[112 705 90 26], ...
        'BackgroundColor', BG_BTN, ...
        'FontColor', FC_LBL,'FontSize',10, ...
        'ButtonPushedFcn',@(~,~) setMode('compare'));

    %% Band buttons and checkboxes
    bandBtns   = gobjects(size(bands,1),1);
    checkboxes = gobjects(size(bands,1),1);

    for i = 1:size(bands,1)
        ypos = 670-(i-1)*62;

        uipanel(leftPanel,'Position',[8 ypos+2 6 22], ...
                'BackgroundColor',colors(i,:), ...
                'BorderColor',    colors(i,:));

        idx = i;

        if i == 7
            btnBG = BG_BTNON;
            btnFC = [1 1 1];
        else
            btnBG = BG_BTN;
            btnFC = colors(i,:) * 0.75;   % slightly darker for contrast on white
        end

        bandBtns(i) = uibutton(leftPanel,'Text',bands{i,1}, ...
            'Position',[20 ypos 105 26], ...
            'BackgroundColor', btnBG, ...
            'FontColor',       btnFC, ...
            'FontSize',11,'FontWeight','bold', ...
            'ButtonPushedFcn',@(~,~) selectBand(idx));

        checkboxes(i) = uicheckbox(leftPanel, ...
            'Text','','Position',[132 ypos+3 25 20], ...
            'Value',false,'FontSize',10, ...
            'ValueChangedFcn',@(~,~) updateCompare());
        checkboxes(i).Visible = 'off';

        freq = bands{i,2};
        if freq >= 1e9
            fStr = sprintf('%.1f GHz',freq/1e9);
        else
            fStr = sprintf('%.0f MHz',freq/1e6);
        end

        nose_v = bandStats(i,1);
        if nose_v < -25
            scol = [0.05 0.55 0.15];   % dark green
        elseif nose_v < -15
            scol = [0.65 0.45 0.00];   % amber
        else
            scol = [0.80 0.10 0.10];   % red
        end

        uilabel(leftPanel,'Text', ...
            sprintf('%s  Nose:%.1f dBsm',fStr,bandStats(i,1)), ...
            'Position',[20 ypos-18 190 16], ...
            'FontSize',8,'FontColor',scol);
    end

    btnSelAll = uibutton(leftPanel,'Text','ALL', ...
        'Position',[10 18 90 26], ...
        'BackgroundColor', BG_BTN, ...
        'FontColor', FC_HDR,'FontSize',10, ...
        'ButtonPushedFcn',@(~,~) selAll());
    btnSelAll.Visible = 'off';

    btnClrAll = uibutton(leftPanel,'Text','CLEAR', ...
        'Position',[115 18 90 26], ...
        'BackgroundColor',[1.0 0.90 0.90], ...
        'FontColor',[0.75 0.10 0.10],'FontSize',10, ...
        'ButtonPushedFcn',@(~,~) clrAll());
    btnClrAll.Visible = 'off';

    %% Stats Panel
    statsPanel = uipanel(fig,'Position',[238 738 1135 48], ...
                         'BackgroundColor', BG_PANEL, ...
                         'BorderColor',     BD_COLOR, ...
                         'Title','STATS', ...
                         'ForegroundColor', FC_HDR);
    statsLabel = uilabel(statsPanel, ...
        'Text','Select a band to view its RCS polar pattern', ...
        'Position',[10 4 1110 24],'FontSize',11, ...
        'FontColor', FC_STAT);

    %% Main Polar Axes
    ax_main = polaraxes(fig,'Position',[0.19 0.07 0.56 0.71]);
    ax_main.Color          = AX_BG;
    ax_main.GridColor      = AX_GRID;
    ax_main.RColor         = AX_TICK;
    ax_main.ThetaColor     = AX_TICK;
    ax_main.LineWidth      = 0.8;
    ax_main.Title.Color    = FC_HDR;
    ax_main.Title.FontSize = 13;
    ax_main.FontSize       = 10;

    %% Info Panel
    infoPanel = uipanel(fig,'Position',[1155 8 218 775], ...
                        'BackgroundColor', BG_PANEL, ...
                        'BorderColor',     BD_COLOR, ...
                        'Title','BAND INFO', ...
                        'ForegroundColor', FC_HDR, ...
                        'FontSize',11);

    infoText = uitextarea(infoPanel, ...
        'Position',[8 8 200 745], ...
        'BackgroundColor', BG_PANEL, ...
        'FontColor',       FC_STAT, ...
        'FontSize',10,'Editable','off', ...
        'Value',{'Select a band','to see details'});

    %% Initial draw
    drawSingle(activeBand);

    %% ======== GPU COMPUTE FUNCTIONS ========

    function rcs_az = computeRCS_GPU(az, k, lambda, ...
                                      normals_g, areas_g, centroids_g)
        numAz  = length(az);
        rcs_az = zeros(1, numAz);

        az_rad = gpuArray(single(deg2rad(az)));
        inc_x  = cos(az_rad);
        inc_y  = sin(az_rad);
        inc_z  = gpuArray(single(zeros(1,numAz)));

        nx = normals_g(:,1);  ny = normals_g(:,2);  nz = normals_g(:,3);
        cx = centroids_g(:,1); cy = centroids_g(:,2); cz = centroids_g(:,3);

        cos_t     = -nx*inc_x - ny*inc_y - nz*inc_z;
        illum     = cos_t > 0;
        inc_dot_c = cx*inc_x + cy*inc_y + cz*inc_z;
        phase     = exp(1j * single(2*k) * inc_dot_c);
        contrib   = single(areas_g) .* cos_t .* illum .* phase;
        rcs_sum   = sum(contrib, 1);

        rcs_sum_cpu = gather(rcs_sum);
        rcs_az = (4*pi/lambda^2) * abs(rcs_sum_cpu).^2;
    end

    function rcs_az = computeRCS_CPU(az, k, lambda, ...
                                      normals, areas, centroids)
        az_rad = deg2rad(az);
        inc_x  = cos(az_rad);
        inc_y  = sin(az_rad);

        nx = normals(:,1);  ny = normals(:,2);
        cx = centroids(:,1); cy = centroids(:,2);

        cos_t     = -nx*inc_x - ny*inc_y;
        illum     = cos_t > 0;
        inc_dot_c = cx*inc_x + cy*inc_y;
        phase     = exp(1j * 2*k * inc_dot_c);
        contrib   = areas .* cos_t .* illum .* phase;
        rcs_sum   = sum(contrib, 1);
        rcs_az    = (4*pi/lambda^2) * abs(rcs_sum).^2;
    end

    %% ======== UI FUNCTIONS ========

    function setMode(mode)
        viewMode = mode;
        if strcmp(mode,'single')
            btnSingle.BackgroundColor  = BG_BTNON;
            btnSingle.FontColor        = [1 1 1];
            btnCompare.BackgroundColor = BG_BTN;
            btnCompare.FontColor       = FC_LBL;
            for i = 1:size(bands,1)
                bandBtns(i).Visible   = 'on';
                checkboxes(i).Visible = 'off';
            end
            btnSelAll.Visible = 'off';
            btnClrAll.Visible = 'off';
            drawSingle(activeBand);
        else
            btnCompare.BackgroundColor = BG_BTNON;
            btnCompare.FontColor       = [1 1 1];
            btnSingle.BackgroundColor  = BG_BTN;
            btnSingle.FontColor        = FC_LBL;
            for i = 1:size(bands,1)
                bandBtns(i).Visible   = 'off';
                checkboxes(i).Visible = 'on';
                checkboxes(i).Value   = false;
            end
            checkboxes(activeBand).Value = true;
            btnSelAll.Visible = 'on';
            btnClrAll.Visible = 'on';
            updateCompare();
        end
    end

    function selectBand(idx)
        activeBand = idx;
        for i = 1:size(bands,1)
            if i == idx
                bandBtns(i).BackgroundColor = BG_BTNON;
                bandBtns(i).FontColor       = [1 1 1];
            else
                bandBtns(i).BackgroundColor = BG_BTN;
                bandBtns(i).FontColor       = colors(i,:) * 0.75;
            end
        end
        drawSingle(idx);
    end

    function drawSingle(idx)
        cla(ax_main);
        rcs_db = bandRCS{idx};
        col    = colors(idx,:);

        hold(ax_main,'on');

        theta_full = [deg2rad(az), deg2rad(az(1))];
        rcs_full   = [rcs_db, rcs_db(1)];
        polarplot(ax_main, theta_full, rcs_full, ...
            'Color', col * 0.6 + 0.4, 'LineWidth', 0.5);   % faint fill line

        polarplot(ax_main, deg2rad(az), rcs_db, ...
            'Color', col, 'LineWidth', 2.5, ...
            'DisplayName', bands{idx,1});

        nose_val = bandStats(idx,1);
        polarplot(ax_main, 0, nose_val, 'o', ...
            'MarkerSize',10, ...
            'MarkerFaceColor',[0.05 0.70 0.20], ...
            'MarkerEdgeColor',[0.05 0.30 0.10], 'LineWidth',1.5, ...
            'DisplayName', sprintf('Nose-on: %.1f dBsm', nose_val));

        side_val = bandStats(idx,2);
        polarplot(ax_main, deg2rad(90), side_val, 's', ...
            'MarkerSize',10, ...
            'MarkerFaceColor',[0.85 0.15 0.10], ...
            'MarkerEdgeColor',[0.40 0.05 0.05], 'LineWidth',1.5, ...
            'DisplayName', sprintf('Broadside: %.1f dBsm', side_val));

        [~,midx] = max(rcs_db);
        polarplot(ax_main, deg2rad(az(midx)), rcs_db(midx), '^', ...
            'MarkerSize',10, ...
            'MarkerFaceColor',[0.95 0.75 0.00], ...
            'MarkerEdgeColor',[0.50 0.35 0.00], 'LineWidth',1.5, ...
            'DisplayName', sprintf('Max: %.1f dBsm @ %d deg', ...
                                   rcs_db(midx), az(midx)));
        hold(ax_main,'off');

        legend(ax_main, 'TextColor', FC_STAT, ...
               'Color', BG_PANEL, ...
               'EdgeColor', BD_COLOR, ...
               'Location','southoutside', ...
               'NumColumns',2, 'FontSize',9);

        freq = bands{idx,2};
        if freq >= 1e9
            fStr = sprintf('%.1f GHz',freq/1e9);
        else
            fStr = sprintf('%.0f MHz',freq/1e6);
        end

        ax_main.Title.String = sprintf('%s  (%s)  —  RCS Polar Pattern', ...
                                        bands{idx,1}, fStr);
        ax_main.Title.Color  = col * 0.7;   % slightly darkened for white bg

        statsLabel.Text = sprintf( ...
            '%s | %s | Nose-on: %.2f dBsm | Broadside: %.2f dBsm | Max: %.2f dBsm @ %d deg | Min: %.2f dBsm', ...
            bands{idx,1}, fStr, ...
            bandStats(idx,1), bandStats(idx,2), ...
            bandStats(idx,3), az(midx), bandStats(idx,4));
        statsLabel.FontColor = col * 0.75;

        updateInfoPanel(idx);
    end

    function updateCompare()
        selected = find(arrayfun(@(cb) cb.Value, checkboxes));
        if isempty(selected)
            cla(ax_main);
            statsLabel.Text      = 'Select bands to compare';
            statsLabel.FontColor = FC_LBL;
            return;
        end

        cla(ax_main);
        hold(ax_main,'on');
        for i = 1:length(selected)
            idx = selected(i);
            polarplot(ax_main, deg2rad(az), bandRCS{idx}, ...
                'Color', colors(idx,:), 'LineWidth', 2.0, ...
                'DisplayName', bands{idx,1});
        end
        hold(ax_main,'off');

        legend(ax_main, 'TextColor', FC_STAT, ...
               'Color', BG_PANEL, ...
               'EdgeColor', BD_COLOR, ...
               'Location','southoutside','NumColumns',5,'FontSize',10);

        ax_main.Title.String = 'RCS Comparison — Selected Bands';
        ax_main.Title.Color  = FC_HDR;

        statsLabel.Text      = sprintf('%d bands selected for comparison', ...
                                        length(selected));
        statsLabel.FontColor = FC_STAT;

        lines = {'=== COMPARISON TABLE ===', ''};
        lines{end+1} = sprintf('%-8s %-8s %-8s %-8s', ...
                                'Band','Nose','Side','Max');
        lines{end+1} = repmat('-',1,36);
        for i = 1:length(selected)
            idx = selected(i);
            lines{end+1} = sprintf('%-8s %+7.2f  %+7.2f  %+7.2f', ...
                bands{idx,1}, ...
                bandStats(idx,1), ...
                bandStats(idx,2), ...
                bandStats(idx,3));
        end
        lines{end+1} = '';
        lines{end+1} = 'GREEN dot = Nose-on';
        lines{end+1} = 'RED sq    = Broadside';
        infoText.Value = lines;
    end

    function updateInfoPanel(idx)
        freq   = bands{idx,2};
        lambda = c/freq;

        if freq >= 1e9
            fStr = sprintf('%.1f GHz',freq/1e9);
        else
            fStr = sprintf('%.0f MHz',freq/1e6);
        end

        nose_v = bandStats(idx,1);

        if nose_v < -25
            stealthStr = 'EXCELLENT';
        elseif nose_v < -15
            stealthStr = 'MODERATE';
        else
            stealthStr = 'HIGH RCS';
        end

        UAV_len = 5.0;
        ratio   = lambda / UAV_len;
        if ratio > 1
            regime = 'Rayleigh';
        elseif ratio > 0.1
            regime = 'Resonance';
        else
            regime = 'Optical';
        end

        gpuStr = 'NO  - CPU Mode';
        if useGPU, gpuStr = 'YES - GPU Active'; end

        lines = {
            sprintf('BAND:   %s',       bands{idx,1}), ...
            sprintf('FREQ:   %s',       fStr), ...
            sprintf('LAMBDA: %.4f m',   lambda), ...
            '', ...
            '--- RCS VALUES ---', ...
            sprintf('Nose-on:   %.2f dBsm', nose_v), ...
            sprintf('Broadside: %.2f dBsm', bandStats(idx,2)), ...
            sprintf('Maximum:   %.2f dBsm', bandStats(idx,3)), ...
            sprintf('Minimum:   %.2f dBsm', bandStats(idx,4)), ...
            '', ...
            '--- STEALTH ---', ...
            sprintf('  %s', stealthStr), ...
            '', ...
            '--- PHYSICS ---', ...
            sprintf('lambda/L = %.3f', ratio), ...
            sprintf('Regime:    %s',   regime), ...
            '', ...
            '--- GPU ACCEL ---', ...
            sprintf('  %s', gpuStr), ...
            '', ...
            '--- THREATS ---', ...
        };

        threats = getThreatInfo(bands{idx,1});
        for t = 1:size(threats,1)
            if nose_v < threats{t,2}
                lines{end+1} = sprintf('%s: SAFE',     threats{t,1});
            else
                lines{end+1} = sprintf('%s: DETECTED', threats{t,1});
            end
        end

        infoText.Value = lines;
    end

    function threats = getThreatInfo(bandName)
        switch bandName
            case 'L-band'
                threats = {'AWACS',-15; 'AEW',-12};
            case 'S-band'
                threats = {'S-300',-20; 'Patriot',-22};
            case 'C-band'
                threats = {'S-300',-20; 'Patriot',-25; 'Hawk',-18};
            case 'X-band'
                threats = {'APG-68',-15; 'Irbis-E',-20};
            case {'Ku-band','K-band','Ka-band'}
                threats = {'Msl.Seeker',-10; 'mmWave',-5};
            otherwise
                threats = {'EarlyWarn',-10};
        end
    end

    function selAll()
        for i = 1:size(bands,1), checkboxes(i).Value = true; end
        updateCompare();
    end

    function clrAll()
        for i = 1:size(bands,1), checkboxes(i).Value = false; end
        updateCompare();
    end

end