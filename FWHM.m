%% analyze_leds_raw8.m
% Read 8-bit .raw images, fit 2D Gaussians to LEDs, compute centroid errors & FWHM
% Outputs CSV summary and displays results for central and upper LED
% Author: Anant

clear; close all; clc;

function analysis(range,exposure,CROP_PAD,DISPLAY_ONE)
%% ========== USER PARAMETERS ==========
inputFolder = sprintf('C:\\Users\\Anant\\OneDrive\\Desktop\\vbn_data\\vbn_data\\range_%d\\exp%d', range, exposure);
% Point to a folder containing many .raw files, e.g. range_233/

IMG_W = 1200;    % <<-- set image width (pixels)
IMG_H = 800;    % <<-- set image height (pixels)
MEAN_CENTROID_ERROR=0;
mean_cent_errors=[];
mean_gauss_peak_val =0;
% processing parameters
THRESH = 20;        % threshold for simple binarization (tune)
MIN_AREA =10;      % minimum blob area to consider


%% ========== FIND RAW FILES ==========
files = dir(fullfile(inputFolder, '*.dng'));
if isempty(files)
    error('No .raw files found in %s. Check path and filenames.', inputFolder);
end

% Prepare results table
results = [];
header = {'filename','led_role','gauss_x','gauss_y','sigma_x','sigma_y','FWHM_px','centroid_x','centroid_y','peak of gauss','blob area','centroid_to_gauss_dist'};

%% ========== MAIN LOOP ==========
for i = 1:3
  outputCSV = fullfile(inputFolder, sprintf('led_analysis_summary_moment_%d.csv', i));
for fi = 1:numel(files)
    fname = fullfile(files(fi).folder, files(fi).name);
    fprintf('Processing %s (%d/%d)\n', files(fi).name, fi, numel(files));
    
    % ---------- Read raw 8-bit image ----------
    I16 = rawread(fname);   % returns uint8 (IMG_H x IMG_W)
    I = uint8(I16/256) ;
    %imshow(I,[]);
    I = double(I);  % work in double for fitting
    
    % ---------- Preprocess and detect blobs ----------
    % simple local thresholding; you may replace with your own centroiding
    BW = I > THRESH;
    BW = bwareaopen(BW, MIN_AREA);
    
    % label components
    CC = bwconncomp(BW, 8);
    stats = regionprops(CC, I.^2, 'Centroid','Area','BoundingBox','PixelIdxList','WeightedCentroid');
    
    % require at least 5 blobs; else skip
    if numel(stats) < 3
        fprintf('  Found %d blobs < 3; skipping file.\n', numel(stats));
        continue;
    end
    
    % Build list of blobs with intensity-weighted centroid and bounding boxes
    blobs = struct('bbox',[],'wcent',[0 0],'area',0,'idx',[],'mask',[]);
    nb = numel(stats);
    for k = 1:nb
        blobs(k).bbox = stats(k).BoundingBox;   % [x y w h]
        blobs(k).wcent = stats(k).WeightedCentroid;
        blobs(k).area = stats(k).Area;
        blobs(k).idx  = stats(k).PixelIdxList;
    end
    
    % If we have more than 5 (noise), keep the 5 brightest by max intensity inside blob
    if numel(blobs) > 5
        meanInt = zeros(1,numel(blobs));
        for k=1:numel(blobs)
            meanInt(k) = mean(I(blobs(k).idx));
        end
        [~, ord] = sort(meanInt, 'descend');
        keep = ord(1:5);
        blobs = blobs(keep);
    end
    
    % If fewer than 5 but >=3, still proceed (will only process found blobs)
    
    % ---------- Fit 2D Gaussian to each blob ----------
    nBlobs = numel(blobs);
    fits = struct('x0',[],'y0',[],'sx',[],'sy',[],'amp',[],'offset',[],'FWHM',[],'centroid',[]);
    for k = 1:nBlobs
        % bounding box crop with padding
        bb = blobs(k).bbox; % [x y w h] (1-based)
        x1 = max(1, floor(bb(1)) - CROP_PAD);
        y1 = max(1, floor(bb(2)) - CROP_PAD);
        x2 = min(IMG_W, ceil(bb(1)+bb(3)) + CROP_PAD);
        y2 = min(IMG_H, ceil(bb(2)+bb(4)) + CROP_PAD);
        crop = I(y1:y2, x1:x2);

        %disp(numel(crop));
        [h0,w0] = size(crop);
        [X,Y] = meshgrid(1:w0, 1:h0);
        
        % initial param guesses [amp, x0, y0, sx, sy, offset]
        [wcx, wcy] = deal(blobs(k).wcent(1) - x1 + 1, blobs(k).wcent(2) - y1 + 1); % relative to crop
        amp0 = double(max(crop(:)) - min(crop(:)));
        sx0 = max(1, min(w0,h0)/6);
        sy0 = sx0;
        off0 = double(min(crop(:)));
        p0 = [amp0, wcx, wcy, sx0, sy0, off0];
    %disp (wcx);
    %disp(off0);
    %disp (amp0);
    %disp (p0);
        % objective: sum squared error
        fun = @(p) gaussian2d_residuals(p, X, Y, crop);
        
        % use fminsearch to minimize SSE
        options = optimset('Display','off','MaxIter',1000,'TolX',1e-4,'TolFun',1e-4);
        try
            pbest = fminsearch(fun, p0, options);
        catch
            pbest = p0;
        end
       
        amp = max(0, pbest(1));
        x0 = pbest(2);
        y0 = pbest(3);
        sx = max(0.1, pbest(4));
        sy = max(0.1, pbest(5));
        off = pbest(6);
        
        % convert to global image coordinates
        gx = x0 + x1 - 1;
        gy = y0 + y1 - 1;
        
        % FWHM: for each axis FWHM = 2*sqrt(2*ln2)*sigma = 2.35482*sigma
        FWHM_x = 2.354817419 * sx;
        FWHM_y = 2.354817419 * sy;
        FWHM_mean = sqrt(mean([FWHM_x^2, FWHM_y^2]));
        
        % intensity-weighted centroid (from region)
        pixelIdx = blobs(k).idx;
        [py,px] = ind2sub([IMG_H, IMG_W], pixelIdx);
        intens = I(pixelIdx);
        intens = intens.^i ;
        if sum(intens) > 0
            cx = sum(double(px).*double(intens))/sum(double(intens));
            cy = sum(double(py).*double(intens))/sum(double(intens));
        else
            cx = blobs(k).wcent(1);
            cy = blobs(k).wcent(2);
        end
        
        fits(k).x0 = gx;
        fits(k).y0 = gy;
        fits(k).sx = sx;
        fits(k).sy = sy;
        fits(k).amp = amp;
        fits(k).offset = off;
        fits(k).FWHM = FWHM_mean;
        fits(k).centroid = [cx, cy];
        fits(k).cropBox = [x1,y1,x2,y2];
    end
    
    % ---------- Identify central LED and upper LED ----------
    % central = blob closest to image center
    imgCenter = [IMG_W/2, IMG_H/2];
    distsToCenter = zeros(1,nBlobs);
    for k=1:nBlobs
        distsToCenter(k) = sqrt( (fits(k).x0 - imgCenter(1))^2 + (fits(k).y0 - imgCenter(2))^2 );
    end
    [~, idxCentral] = min(distsToCenter);
    
    % upper LED = blob with smallest y coordinate (topmost)
    ys = arrayfun(@(s) s.y0, fits);
    [~, idxUpper] = min(ys);
    
    % ---------- Save results for central and upper (if exist) ----------
    roles = {'central'}; %{'central','upper'};
    idxs = [idxCentral, idxUpper];
    for r = 1:1
        idxk = idxs(r);
        if isempty(idxk) || idxk < 1 || idxk > nBlobs
            continue;
        end
        gauss_x = fits(idxk).x0;
        gauss_y = fits(idxk).y0;
        sx = fits(idxk).sx;
        sy = fits(idxk).sy;
        FWHM_px = fits(idxk).FWHM;
        cx = fits(idxk).centroid(1);
        cy = fits(idxk).centroid(2);
        peak = fits(idxk).amp;
        dist_cg = sqrt( (cx - gauss_x)^2 + (cy - gauss_y)^2 ); 
        MEAN_CENTROID_ERROR= MEAN_CENTROID_ERROR + dist_cg/60;
        mean_gauss_peak_val = peak + mean_gauss_peak_val;
        % append to results
        results = [results; {files(fi).name, roles{r}, gauss_x, gauss_y, sx, sy, FWHM_px, cx, cy,peak,blobs(idxCentral).area, dist_cg}];
    end
    
    % ---------- optional display for first file ----------
    if DISPLAY_ONE && fi==60
        figure(1); clf;
        imshow(uint8(I), []);
        hold on;
        for k=1:nBlobs
            plot(fits(k).x0, fits(k).y0, 'r+','MarkerSize',10,'LineWidth',1.5);
            plot(fits(k).centroid(1), fits(k).centroid(2), 'go','MarkerSize',8,'LineWidth',1.2);
            rectangle('Position',[fits(k).cropBox(1),fits(k).cropBox(2), ...
                fits(k).cropBox(3)-fits(k).cropBox(1)+1, fits(k).cropBox(4)-fits(k).cropBox(2)+1], ...
                'EdgeColor','y');
        end
        legend('Gaussian mean','Centroid','Crop box');
        title(['Example fits: ' files(fi).name]);
    end

end
    
%% ========== Mean values across images ==========
    mean_cent_errors = [mean_cent_errors,MEAN_CENTROID_ERROR];
    MEAN_CENTROID_ERROR=0;
    
%% ========== WRITE CSV ==========
if ~isempty(results)
    T = cell2table(results, 'VariableNames', header);
    writetable(T, outputCSV);
    fprintf('Saved summary to %s (%d rows)\n', outputCSV, size(T,1));
else
    fprintf('No results produced.\n');
end
end
disp (mean_gauss_peak_val/180);
disp (mean_cent_errors);
end
%% ========== HELPER FUNCTIONS ==========
function sse = gaussian2d_residuals(p, X, Y, Z)
    % p = [amp, x0, y0, sx, sy, offset]
    amp = p(1); x0 = p(2); y0 = p(3); sx = max(0.0001,p(4)); sy = max(0.0001,p(5)); off = p(6);
    G = amp .* exp( - ( ((X-x0).^2)./(2*sx^2) + ((Y-y0).^2)./(2*sy^2) ) ) + off;
    R = G - double(Z);
    sse = sum(R(:).^2);
end

Ranges = [0,233,466,699];
Exposures = [20,50,100,200];
CROP_PAD = [10,8,5,2];      % padding around each detected blob when fitting
DISPLAY_ONE = true; % true to show example fit for first file
%% ========== Generate data for all files ==========
delete(gcp('nocreate'))
parpool;
jobs = {};
for r = 1:numel(Ranges)
    for e = Exposures
        jobs{end+1} = [Ranges(r), e,CROP_PAD(r)];
    end
end

parfor j = 1:numel(jobs)
    range    = jobs{j}(1);
    exposure = jobs{j}(2);
     crop_pad = jobs{j}(3);
    analysis(range, exposure,crop_pad,false);
end

%% ========== Any specific file data  ==========
%analysis(699,200,3,true);