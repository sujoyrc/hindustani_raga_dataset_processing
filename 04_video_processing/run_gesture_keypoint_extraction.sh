#!/bin/sh

json_dir='../01_json_files'
tar_extracted_directory='../01_json_files/extracted_from_tarGz'
output_directory='../05_video_processing_output/'

mkdir -p ${tar_extracted_directory}

for each_tar_gz in `ls ${json_dir}/*.tar.gz`
do
    echo ${each_tar_gz}
    tar -zxvf ${json_dir}/${each_tar_gz} --directory ${tar_extracted_directory}
done

python process_all_jsons_in_directory.py ${tar_extracted_directory} ${output_directory}
