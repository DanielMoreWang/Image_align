import json
import cv2
import numpy as np
import os

final_width = 640
final_height = 512

def get_sorted_filenames_by_timestamp(folder_path):
    # 获取文件夹下的所有文件名
    filenames = get_sorted_filenames_by_creation_time(folder_path)
    # 将文件名按时间戳从小到大排序
    sorted_filenames = sorted(filenames, key=lambda x: float(x.split('.')[0]))

    return sorted_filenames

def get_sorted_filenames_by_creation_time(folder_path):
    # 获取文件夹下的所有文件名
    filenames = os.listdir(folder_path)

    # 构建文件名和文件创建时间的映射关系
    file_time_map = {}
    for filename in filenames:
        if filename == ".DS_Store":
            continue
        file_path = os.path.join(folder_path, filename)
        file_creation_time = os.path.getctime(file_path)
        file_time_map[filename] = file_creation_time

    # 按照文件创建时间进行排序
    sorted_filenames = sorted(file_time_map.keys(), key=lambda x: file_time_map[x],reverse=True)

    return sorted_filenames

def extract_bounding_box_coordinates(json_file_path):
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    bounding_boxes = []
    x1, y1 = data['shapes'][0]['points'][0]
    x2, y2 = data['shapes'][0]['points'][1]
    # Convert to xyxy format: [x1, y1, x2, y2]
    x1_ = min(x1, x2)
    x2_ = max(x1,x2)

    y1_ = min(y1,y2)
    y2_ = max(y1,y2)

    bounding_boxes.append([x1_, y1_, x2_, y2_])   # x:width, y:height
    # bounding_boxes.append([y1, x1, y2, x2])
    return bounding_boxes

def read_boxes(time_stamp, json_path):
    file_name = str(time_stamp)+ ".json"
    json_file_path = os.path.join(json_path, file_name)
    if os.path.exists(json_file_path) is not True:
        return 0
    else:
        bounding_box = extract_bounding_box_coordinates(json_file_path)
        return bounding_box
    
def crop_align(img_1, box_1,img_2,box_2):
    
    box_1 = [int(item) for item in box_1[0]]
    box_2 = [int(item) for item in box_2[0]]

    certain_point_1 = (int(0.5*(box_1[1]+box_1[3])),box_1[0]) #(height, width)
 
    certain_point_2 = (int(0.5*(box_2[1]+box_2[3])),box_2[0]) #(height, width)

    wid_distance_1 = box_1[2] - box_1[0]
    wid_distance_2 = box_2[2] - box_2[0]
    scale_ratio = wid_distance_1 / wid_distance_2

    img_2_height, img_2_width = img_2.shape[0], img_2.shape[1]
    target_height = int(scale_ratio * img_2_height)
    target_width = int(scale_ratio * img_2_width)
    scale_img = cv2.resize(img_2, (target_width,target_height))

    scale_certain_point_2 = (int(scale_ratio * certain_point_2[0]),int(scale_ratio * certain_point_2[1]))  #(height, width)
    # scale_img = np.array(scale_img)

    crop_y1 = scale_certain_point_2[0]-certain_point_1[0]
    crop_y2 = scale_certain_point_2[0] + (final_height-certain_point_1[0] )

    crop_x1 = scale_certain_point_2[1]-certain_point_1[1]
    crop_x2 = scale_certain_point_2[1] + (final_width-certain_point_1[1] )

    # crop_img = scale_img[crop_x1:crop_x2,crop_y1:crop_y2,:]
    crop_y1_ = min(crop_y1,crop_y2)
    crop_y2_ = max(crop_y1, crop_y2)

    crop_x1_ = min(crop_x1,crop_x2)
    crop_x2_ = max(crop_x1,crop_x2)
    crop_img = scale_img[crop_y1_:crop_y2_,crop_x1_:crop_x2_,:]
    crop_img = cv2.resize(crop_img, (final_width,final_height))
    return crop_img

rgb_dir = "path/to/raw/RGB"
thermal_dir = "path/to/raw/thermal"

sorted_file_names = (get_sorted_filenames_by_timestamp)(thermal_dir)

# print(len(sorted_file_names))

rgb_json_dir = "/path/for/rgb/json/files"
thermal_json_dir = "/path/for/thermal/json/files"

save_cropped_path = "/path/to/save/the/cropped/files"

save_cated_path = "/Users/mac/Desktop/my_work/Yolo_align/file/concated_images"
length = len(sorted_file_names)

for i in range(length):

    rgb_img = cv2.imread(os.path.join(rgb_dir, sorted_file_names[i]))
    t_img = cv2.imread(os.path.join(thermal_dir, sorted_file_names[i]))

    if rgb_img is None or t_img is None:
        print("Read Images error")
        continue
    time_stamp = sorted_file_names[i][:-4]
    rgb_box = read_boxes(time_stamp, rgb_json_dir)
    thermal_box = read_boxes(time_stamp, thermal_json_dir)
    if rgb_box == 0 or thermal_box == 0:
        print("Read Boxes fail!!!")
        continue
    t_cropped_img = crop_align(rgb_img,rgb_box, t_img, thermal_box)


    cropped_file_path = os.path.join(save_cropped_path, sorted_file_names[i][:-4]+".png")
    cv2.imwrite(cropped_file_path, t_cropped_img)


    print("Thermal Image %d  is cropped!" %i )



