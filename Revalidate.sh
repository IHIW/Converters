source venv/bin/activate

declare -a FileList=("filename.hml")
 
for val in "${FileList[@]}"; do
   echo $val
   python testRestMethods.py --task="REVALIDATE_UPLOAD" --bucket="ihiw-management-upload-prod" --verbose --upload="$val"
   sleep 1
done

deactivate
