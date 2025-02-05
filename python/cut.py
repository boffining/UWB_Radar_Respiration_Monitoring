import math
import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.io

import warnings

warnings.filterwarnings("ignore")

# Raw data extraction from .dat file ======================================
dir_path = "./../Data/2023.01.10/2023.01.10_5_soo_jin"

UWB_data_path = dir_path + "/UWB_sync.npy"
BIOPAC_data_path = dir_path + "/BIOPAC_sync.npy"
sample_count = 0
sample_drop_period = 434  # 해당 번째에 값은 사용 안 한다.
end_idx = 0

BIOPAC_data = np.load(BIOPAC_data_path, allow_pickle=True)
BIOPAC_data_1 = BIOPAC_data[0]
BIOPAC_fs_1 = BIOPAC_data[1]
BIOPAC_data_2 = BIOPAC_data[2]
BIOPAC_fs_2 = BIOPAC_data[3]
    
if os.path.exists(UWB_data_path):
    rawdata = np.load(UWB_data_path)
else:
    print("싱크 안맞춤")
fast_to_m = 0.006445  # fast index to meter
UWB_Radar_index_start = 0.5  # UWB Radar Range 0.5 ~ 2.5m
UWB_Radar_index_start = math.floor(UWB_Radar_index_start / fast_to_m)

Window_rawdata = np.array(rawdata[:, 1200:2400])
SD = np.array([])
for i in range(len(Window_rawdata)):
    SD = np.append(SD, np.std(Window_rawdata[i]))  # 거리에 대한 표준편차 배열
Max = max(SD)  # 가장 큰 표준편차 값
Index = np.argmax(SD)  # 가장 큰 표준편차 Idx : MAX 위치 값
Pm = np.mean(SD[Index - 2:Index + 1])  # 가장 높은 표쥰 편차와 -1, +1 idx의 평균값
Index = Index + UWB_Radar_index_start

d0 = Index * fast_to_m  # 가장 높은 편차의 거리 meter
n = np.mean(SD)  # 편차 배열의 평균

baselineThreashold = (Pm - n) / (2 * d0 + 1) + n

# Dynamic Threshold ===========================================================================
di = np.arange(1, len(rawdata) + 1, 1)
di = di + UWB_Radar_index_start
di = di * fast_to_m

k = np.array([])
for i in range(len(di)):
    k = np.append(k, di[i] ** 2 / d0 ** 2)
k = k ** (-1)
Dynamic_threshold = np.array(k) * baselineThreashold

plt.figure(num=1,figsize=(10, 8))
plt.title("Dynamic Threshold and Standard deviation of raw data")
plt.plot(Dynamic_threshold)
plt.plot(SD)
plt.xlabel("Distance")
plt.ylabel("standard deviation")
plt.legend(["Dynamic_threshold","Standard deviation of raw data"])

TC_matrix = np.array([])
Distance = np.zeros((0, 2))

TC_matrix = SD >= Dynamic_threshold

for i in range(len(TC_matrix)):
    if TC_matrix[i] == 0 and (i > 2) and (i < len(TC_matrix) - 1):
        if TC_matrix[i - 1] == 1 and TC_matrix[i + 1] == 1:
            TC_matrix[i] = 1

TC_cnt = 0
Human_cnt = 0
Human = 2

dynamic_TC = 16
while Human_cnt < Human:
    print("Human_cnt:%d Dynamic_TC:%d" % (Human_cnt, dynamic_TC))
    if dynamic_TC == 1: break
    Human_cnt = 0
    dynamic_TC -= 1
    TC_cnt = 0

    TC_matrix = SD >= Dynamic_threshold

    for i in range(len(TC_matrix)):
        if TC_matrix[i] == 0 and (i > 2) and (i < len(TC_matrix) - 1):
            if TC_matrix[i - 1] == 1 and TC_matrix[i + 1] == 1:
                TC_matrix[i] = 1

    for i in range(len(rawdata)):
        if TC_matrix[i]:
            TC_cnt += 1
        else:
            if TC_cnt < dynamic_TC:
                TC_matrix[i - TC_cnt: i] = 0
                TC_cnt = 0
            elif TC_cnt > 75:
                TC_matrix[i - TC_cnt: i] = 0
                TC_cnt = 0
            else:
                Human_cnt += 1
                Distance = np.r_[Distance, [[0, 0]]]
                Distance[Human_cnt - 1, :] = [i - TC_cnt, i - 1]
                TC_cnt = 0
    if TC_cnt != 0:
        if TC_cnt < dynamic_TC:
            TC_matrix[i - TC_cnt:] = 0
            TC_cnt = 0
        elif TC_cnt > 75:
            TC_matrix[i - TC_cnt:] = 0
            TC_cnt = 0
        else:
            Human_cnt += 1
            Distance = np.r_[Distance, [[0, 0]]]
            Distance[Human_cnt - 1, :] = [i - TC_cnt, i - 1]
            TC_cnt = 0

Max_sub = np.zeros((Human_cnt, 1))
Max_sub_Index = np.zeros((Human_cnt, 1))
for i in range(Human_cnt):
    Max_sub[i, 0] = max(SD[int(Distance[i, 0]) - 1:int(Distance[i, 1])])
    Max_sub_Index[i, 0] = np.argmax(SD[int(Distance[i, 0]) - 1:int(Distance[i, 1])])

    Max_sub_Index[i, 0] += Distance[i, 0]
    for i in range(Human_cnt):
        Max_sub[i, 0] = max(SD[int(Distance[i, 0]) - 1:int(Distance[i, 1])])
        Max_sub_Index[i, 0] = np.argmax(SD[int(Distance[i, 0]) - 1:int(Distance[i, 1])])

        Max_sub_Index[i, 0] += Distance[i, 0]

        if len(rawdata) < Max_sub_Index[i, 0] + 15:
            Distance[i, 0] = Max_sub_Index[i, 0] - 15
            Distance[i, 1] = len(rawdata[1])
        elif Max_sub_Index[i, 0] - 15 < 1:
            Distance[i, 0] = 1
            Distance[i, 1] = Max_sub_Index[i, 0] + 15
        else:
            Distance[i, 0] = Max_sub_Index[i, 0] - 15
            Distance[i, 1] = Max_sub_Index[i, 0] + 15

Data = TC_matrix.reshape(TC_matrix.size, 1) * rawdata
fs = 20
show_idx = 60 # 데이터들의 시작부터 몇초 볼껀지
# Print the detected peaks

if Human_cnt > 2:
    Human_cnt = 2 #2명보다 많으면 2명으로 고정(임시) -최광진

for i in range(Human_cnt):
    UWB_data = rawdata[Max_sub_Index[i, 0].astype(int)][:fs * show_idx]
    plt.figure(num=2, figsize=(10, 8))
    plt.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.2, hspace=0.5)
    plt.subplot(Human_cnt, 1, 1 + i)
    plt.subplot(Human_cnt, 1, 1 + i).set_title("UWB Peak Detection " + "Human " + str(i + 1) +"_" + str(Max_sub_Index[i, 0]))
    plt.plot(UWB_data)
    plt.xlabel("Time")
    plt.ylabel("Amplitude")

plt.figure(num=3, figsize=(10, 8))
plt.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.2, hspace=0.5)
plt.subplot(2, 1, 1)
plt.subplot(2, 1, 1).set_title("BIOPAC Peak Detection Data1")
plt.plot(BIOPAC_data_1[:BIOPAC_fs_1*show_idx])
plt.xlabel("Time")
plt.ylabel("Amplitude")

plt.subplot(2, 1, 2)
plt.subplot(2, 1, 2).set_title("BIOPAC Peak Detection Data2")
plt.plot(BIOPAC_data_2[:BIOPAC_fs_2*show_idx])
plt.xlabel("Time")
plt.ylabel("Amplitude")
plt.show()

cut_idx = int(input("UWB Rawdata 그래프를 참고하여 자를 부분에 index를 입력하시오 "))
UWB_cut_path = dir_path + "/UWB_cut.npy"
BIOPAC_cut_path = dir_path + "/BIOPAC_cut.npy"

BIOPAC_cut = []
UWB_cut = rawdata[:,cut_idx:]
BIOPAC_cut.append(BIOPAC_data_1[int(cut_idx*BIOPAC_fs_1/fs):])
BIOPAC_cut.append(BIOPAC_fs_1)
BIOPAC_cut.append(BIOPAC_data_2[int(cut_idx*BIOPAC_fs_2/fs):])
BIOPAC_cut.append(BIOPAC_fs_2)

np.save(UWB_cut_path,UWB_cut)
BIOPAC_cut = np.array(BIOPAC_cut,dtype="object")
np.save(BIOPAC_cut_path, BIOPAC_cut)