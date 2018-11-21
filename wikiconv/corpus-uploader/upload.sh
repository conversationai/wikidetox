#!/bin/bash
# exit script if any command fails
set -e
. config/figshare_token.config


#modify BASE_URL, ACCESS_TOKEN, FILE_NAME and FILE_PATH according to your needs
BASE_URL='https://api.figshare.com/v2/account/articles'

CLOUD_URL=$CLOUD_URL$LANGUAGE

#gsutil ls 'gs://'$CLOUD_URL > 'tmp/filelist'

for name in `cat tmp/filelist`; do
  echo $name
  tmpfile=$(basename $name)
  echo $tmpfile
  gsutil cp $name 'tmp/'

  FILE_NAME=$tmpfile
  FILE_PATH='tmp/'$FILE_NAME
  
  
  #Retrieve the file size and MD5 values for the item which needs to be uploaded
  FILE_SIZE=$(stat -c%s $FILE_PATH)
  MD5=$(md5sum $FILE_PATH)
  echo $MD5
  
  
  # List all of the existing items
  #echo 'List all of the existing items...'
  RESPONSE=$(curl -s -f -H 'Authorization: token '$ACCESS_TOKEN -X GET "$BASE_URL")
  #echo "The item list dict contains: "$RESPONSE
  #echo ''
  
  # Create a new item
  echo 'Creating a new item...'
  RESPONSE=$(curl -s -d '{"title": "'${FILE_NAME}'"}' -H 'Authorization: token '$ACCESS_TOKEN -H 'Content-Type: application/json' -X POST "$BASE_URL")
  echo "The location of the created item is "$RESPONSE
  echo ''
  
  # Retrieve item id
  echo 'Retrieving the item id...'
  ITEM_ID=$(echo "$RESPONSE" | sed -r "s/.*\/([0-9]+).*/\1/")
  echo "The item id is "$ITEM_ID
  echo ''
  
  # List item files
  echo 'Retrieving the item files...'
  FILES_LIST=$(curl -s -f -H 'Authorization: token '$ACCESS_TOKEN -X GET "$BASE_URL/$ITEM_ID/files")
  echo 'The files list of the newly-create item should be an empty one. Returned results: '$FILES_LIST
  echo ''
  
  # Initiate new upload:
  echo 'A new upload had been initiated...'
  echo '{"md5": "'${MD5}'", "name": "'${FILE_NAME}'"}'
  RESPONSE=$(curl -s -d '{"name": "'${FILE_NAME}'", "size": '${FILE_SIZE}'}' -H 'Content-Type: application/json' -H 'Authorization: token '$ACCESS_TOKEN -X POST "$BASE_URL/$ITEM_ID/files")
  echo $RESPONSE
  echo ''
  
  # Retrieve file id
  echo 'The file id is retrieved...'
  FILE_ID=$(echo "$RESPONSE" | sed -r "s/.*\/([0-9]+).*/\1/")
  echo 'The file id is: '$FILE_ID
  echo ''
  
  # Retrieve the upload url
  echo 'Retrieving the upload URL...'
  RESPONSE=$(curl -s -H 'Authorization: token '$ACCESS_TOKEN -X GET "$BASE_URL/$ITEM_ID/files/$FILE_ID")
  UPLOAD_URL=$(echo "$RESPONSE" | sed -r 's/.*"upload_url":\s"([^"]+)".*/\1/')
  echo 'The upload URL is: '$UPLOAD_URL
  echo ''
  
  # Retrieve the upload parts
  echo 'Retrieving the part value...'
  RESPONSE=$(curl -s -f -H 'Authorization: token '$ACCESS_TOKEN -X GET "$UPLOAD_URL")
  PARTS_SIZE=$(echo "$RESPONSE" | sed -r 's/"endOffset":([0-9]+).*/\1/' | sed -r 's/.*,([0-9]+)/\1/')
  PARTS_SIZE=$(($PARTS_SIZE+1))
  echo 'The part value is: '$PARTS_SIZE
  echo ''
  
  
  # Split item into needed parts
  echo 'Spliting the provided item into parts process had begun...'
  split -b$PARTS_SIZE $FILE_PATH part_ --numeric=1
  
  echo 'Process completed!'
  
  # Retrive the number of parts
  MAX_PART=$((($FILE_SIZE+$PARTS_SIZE-1)/$PARTS_SIZE))
  echo 'The number of parts is: '$MAX_PART
  echo ''
  
  # Perform the PUT operation of parts
  echo 'Perform the PUT operation of parts...'
  for ind in `seq 1 $MAX_PART`;#((ind=1; ind<=$MAX_PART; ind++)) do
  do
      PART_VALUE='part_'$i
      if [ "$ind" -le 9 ]
      then
          PART_VALUE='part_0'$i
      fi
      RESPONSE=$(curl -s -H 'Authorization: token '$ACCESS_TOKEN -X PUT "$UPLOAD_URL/$ind" --data-binary @$PART_VALUE)
      echo "Done uploading part nr: $ind/"$MAX_PART
  done
  
  echo 'Process was finished!'
  echo ''
  
  # Complete upload
  echo 'Completing the file upload...'
  RESPONSE=$(curl -s -H 'Authorization: token '$ACCESS_TOKEN -X POST "$BASE_URL/$ITEM_ID/files/$FILE_ID")
  echo 'Done!'
  echo ''
  
  #remove the part files
  rm part_*
  
  # List all of the existing items
  RESPONSE=$(curl -s -H 'Authorization: token '$ACCESS_TOKEN -X GET "$BASE_URL")
  echo 'New list of items: '$RESPONSE
  echo ''

  rm 'tmp/'$tmpfile

done 


