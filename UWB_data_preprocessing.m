%% Raw data extraction from .dat file

clear,clc,close all;


file_name = './Data/0830_광진,윤곤/0830_2nd_광진(1m)_윤곤(1.5m)/xethru_datafloat_20220830_144349.dat';
fid_raw = fopen(file_name,'r');

sample_count = 0;
sample_drop_period = 434;
DataCursor = 1;
rawdata = [];
InputData = [];
while (1)
    id = fread(fid_raw,1,'uint32');
    if length(id) < 1, break; end
    loop_cnt = fread(fid_raw,1,'uint32');
    numCountersFromFile = fread(fid_raw,1,'uint32');
    Data = fread(fid_raw,[1 numCountersFromFile],'real*4');
    %             fprintf('%d, %d, %d\n', id, loop_cnt, numCountersFromFile)

    sample_count = sample_count + 1;
    if mod(sample_count, sample_drop_period) == 0
        continue;
    end

    fInputData = single(Data);
    InputData(:,DataCursor)= double(fInputData); % Raw data
    DataCursor = DataCursor + 1;

end
rawdata = [rawdata InputData];
fid_raw = fclose(fid_raw);
save rawdata.mat rawdata


