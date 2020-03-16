# Manual Execution 

	Project created for demo application: 

	https://github.com/scm-spain/devops-test-helloworld-app

	Pre-requeriments: 

	Python3 
	Boto3
	Aws-cli 

# Installing Boto3 for python: 

	https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
	
	pip3 install boto boto3
	
# Aws IAM Permissions: 
	
	https://aws.amazon.com/iam/features/manage-permissions/
	
	AmazonS3FullAccess
	AmazonEC2FullAccess
	AmazonVPCFullAccess

# Aws-cli installation: 

	https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html


# Aws-cli configuration:

	https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html

	Example: 

	$aws configure

	AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
	AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
	Default region name [None]: us-west-2
	Default output format [None]: json


# Changing the name of the bucket: 

	Replace the variables with the correct information on “userDataCode” 

	ACCESSKEY
	SECRETKEY
	NAMEOFBUCKET

	Name of bucket origin: 
		bucket_name = globalVars['Project']['Value'] + '-s3bucket-' + globalVars['env']['Value']

	sudo echo "ACCESSKEY:SECRETKEY" > /etc/passwd-s3fs
	sudo chmod 600 /etc/passwd-s3fs
	sudo mkdir /var/log/hello-world && sudo s3fs -o nonempty NAMEOFBUCKET /var/log/hello-world


# AWS ID image:

	Amazon Linux 2 AMI (HVM), SSD Volume Type - ami-09a7fe78668f1e2c0


# For production environment of the apps need to do some changes: 

	Set the Environment on the python script (dev to prd): 

	globalVars['env']                      = {'Key': 'Environment', 'Value': 'dev'} 


UserData change for this:  

	#!/bin/bash
	set -e -x
	sudo yum update -y 
	sudo amazon-linux-extras install epel -y 
	sudo yum install s3fs-fuse docker git curl java-1.8.0 java-1.8.0-openjdk-devel -y
	sudo echo "ACCESSKEY:SECRETKEY" > /etc/passwd-s3fs
	sudo chmod 600 /etc/passwd-s3fs
	sudo mkdir /var/log/hello-world && sudo s3fs -o nonempty NAMEOFBUCKET /var/log/hello-world
	sudo usermod -aG docker ec2-user
	sudo service docker start
	sudo chkconfig docker on
	sudo curl -L https://github.com/docker/compose/releases/download/1.25.0/docker-compose-`uname -s`-`uname -m` | sudo tee /usr/local/bin/docker-compose > /dev/null
	sudo chmod +x /usr/local/bin/docker-compose
	sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
	sudo git clone https://github.com/scm-spain/devops-test-helloworld-app
	cd devops-test-helloworld-app 
	sudo ./gradlew build
	sudo java -jar ./build/libs/helloworld-0.0.1-SNAPSHOT.jar --spring.profiles.active=pro

# How to Exec 

	  python3 adevinta-demo.py

