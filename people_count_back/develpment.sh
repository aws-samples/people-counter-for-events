pip install -r requirements.txt -t /home/ec2-user/environment/people_count_back/lambda

REGION=$(aws configure get region)
UUID=$(uuidgen | awk '{print tolower($0)}')
S3_BUCKET=samples-bucket-$UUID
aws s3 mb "s3://${S3_BUCKET}" --region $REGION

cd /home/ec2-user/environment/people_count_back/lambda

#Upload zip lambda file to S3bucket 
zip -r ../index * 

cd /home/ec2-user/environment/people_count_back/

aws s3 cp index.zip "s3://${S3_BUCKET}/"


##deploy backend

aws cloudformation create-stack \
  --stack-name people-count-stack \
  --template-body file:///home/ec2-user/environment/people_count_back/samples.json \
  --parameters ParameterKey=BucketName,ParameterValue=${S3_BUCKET} \
  --capabilities CAPABILITY_NAMED_IAM 

##deploy frontend

cd /home/ec2-user/environment/people_count_front
npm install
