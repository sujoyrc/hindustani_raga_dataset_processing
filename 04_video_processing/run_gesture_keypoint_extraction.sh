#!/bin/sh
#set -x
if [ -z "$CAMERA_VIEWS" ]; then
  echo "CAMERA_VIEWS is not set. Setting to 3D"
  export CAMERA_VIEWS="3D"
elif [ "$CAMERA_VIEWS" != "3D" ] && [ "$CAMERA_VIEWS" != "2D" ]; then
  echo "CAMERA_VIEWS variable must be either 2D or 3D. This is set to $CAMERA_VIEWS"
  exit 1
fi
if [ "$CAMERA_VIEWS" = "2D" ]; then
	json_dir='../01_json_files'
	tar_extracted_directory='../01_json_files/'
	output_directory='../05_video_processing_output/'

	mkdir -p ${tar_extracted_directory}

	for each_tar_gz in `ls -1 ${json_dir}/*.tar.gz`
	do
	    echo ${each_tar_gz}
	    tar -zxvf ${json_dir}/${each_tar_gz} --directory ${tar_extracted_directory}
	done

	python processKeypoints.py $CAMERA_VIEWS
#python process_all_jsons_in_directory.py ${tar_extracted_directory} ${output_directory}
else
	python processKeypoints.py 3D
fi
