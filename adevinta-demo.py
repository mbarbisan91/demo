#!/usr/bin/python

# Check if the user has the Access & Secret key configured
import boto3
import logging

from boto3 import Session
from botocore.exceptions import ClientError
client = boto3.client('s3')
s3 = boto3.client('s3')
ec2 = boto3.resource('ec2')

session = Session()
credentials = session.get_credentials()
current_credentials = credentials.get_frozen_credentials()

# Break & Exit if any of the key is not present
if current_credentials.access_key is None:
    print("Access Key missing, use  `aws configure` to setup")
    exit()

if current_credentials.secret_key is None:
    print("Secret Key missing, use  `aws configure` to setup")
    exit()

# VPC design for multi az deployments
globalVars = {}
globalVars['REGION_NAME']              = "us-west-1"
globalVars['AZ1']                      = "us-west-1a"
globalVars['AZ2']                      = "us-west-1b"
globalVars['CIDRange']                 = "10.240.0.0/23"
globalVars['az1_pvtsubnet_CIDRange']   = "10.240.0.0/25"
globalVars['az1_pubsubnet_CIDRange']   = "10.240.0.128/26"
globalVars['az1_sparesubnet_CIDRange'] = "10.240.0.192/26"
globalVars['az2_pvtsubnet_CIDRange']   = "10.240.1.0/25"
globalVars['az2_pubsubnet_CIDRange']   = "10.240.1.128/26"
globalVars['az2_sparesubnet_CIDRange'] = "10.240.1.192/26"
globalVars['Project']                  = { 'Key': 'Name',        'Value': 'adevinta-demo'}
globalVars['env']                      = {'Key': 'Environment', 'Value': 'dev'} 
globalVars['tags']                     = [{'Key': 'Owner',       'Value': 'codermaster'},
                                          {'Key': 'Environment', 'Value': 'dev'},
                                          {'Key': 'Department',  'Value': 'adevinta-demo'}]
# EC2 Parameters
globalVars['EC2-Amazon-AMI-ID']        = "ami-09a7fe78668f1e2c0" 
globalVars['EC2-InstanceType']         = "t2.micro"
globalVars['EC2-KeyName']              = globalVars['Project']['Value']+'-Key'

# AutoScaling Parameters
globalVars['ASG-LaunchConfigName']     = "ASG-Test-LaunchConfig"
globalVars['ASG-AutoScalingGroupName'] = "ASG-Test-AutoScalingGrp"

# RDS Parameters
globalVars['RDS-DBIdentifier']         = "TestDb01"
globalVars['RDS-Engine']               = "postgres"
globalVars['RDS-DBName']               = "hello_world"
globalVars['RDS-DBMasterUserName']     = "postgres"
globalVars['RDS-DBMasterUserPass']     = "test123456"
globalVars['RDS-DBInstanceClass']      = "db.t2.micro"
globalVars['RDS-DBSubnetGroup']        = "RDS-TEST-DB-Subnet-Group"

# Creating a VPC, Subnet, and Gateway
ec2       = boto3.resource('ec2', region_name=globalVars['REGION_NAME'])
ec2Client = boto3.client('ec2',   region_name=globalVars['REGION_NAME'])
vpc       = ec2.create_vpc(CidrBlock=globalVars['CIDRange'])
asgClient = boto3.client('autoscaling', region_name=globalVars['REGION_NAME'])
rds       = boto3.client('rds', region_name=globalVars['REGION_NAME'])

# AZ1 Subnet
az1_pvtsubnet   = vpc.create_subnet(CidrBlock=globalVars['az1_pvtsubnet_CIDRange'],   AvailabilityZone=globalVars['AZ1'])
az1_pubsubnet   = vpc.create_subnet(CidrBlock=globalVars['az1_pubsubnet_CIDRange'],   AvailabilityZone=globalVars['AZ1'])
az1_sparesubnet = vpc.create_subnet(CidrBlock=globalVars['az1_sparesubnet_CIDRange'], AvailabilityZone=globalVars['AZ1'])
# AZ2 Subnet
az2_pvtsubnet   = vpc.create_subnet(CidrBlock=globalVars['az2_pvtsubnet_CIDRange'],   AvailabilityZone=globalVars['AZ2'])
az2_pubsubnet   = vpc.create_subnet(CidrBlock=globalVars['az2_pubsubnet_CIDRange'],   AvailabilityZone=globalVars['AZ2'])
az2_sparesubnet = vpc.create_subnet(CidrBlock=globalVars['az2_sparesubnet_CIDRange'], AvailabilityZone=globalVars['AZ2'])

# Enable DNS Hostnames in the VPC
vpc.modify_attribute(EnableDnsSupport={'Value': True})
vpc.modify_attribute(EnableDnsHostnames={'Value': True})

# Create the Internet Gatway & Attach to the VPC
intGateway = ec2.create_internet_gateway()
intGateway.attach_to_vpc(VpcId=vpc.id)

# Create another route table for Public & Private traffic
routeTable = ec2.create_route_table(VpcId=vpc.id)
rtbAssn=[]
rtbAssn.append(routeTable.associate_with_subnet(SubnetId=az1_pubsubnet.id))
rtbAssn.append(routeTable.associate_with_subnet(SubnetId=az1_pvtsubnet.id))
rtbAssn.append(routeTable.associate_with_subnet(SubnetId=az2_pubsubnet.id))
rtbAssn.append(routeTable.associate_with_subnet(SubnetId=az2_pvtsubnet.id))

# Create a route for internet traffic to flow out
intRoute = ec2Client.create_route(RouteTableId=routeTable.id, DestinationCidrBlock='0.0.0.0/0', GatewayId=intGateway.id)

# Tag the resources
vpc.create_tags            (Tags=globalVars['tags'])
az1_pvtsubnet.create_tags  (Tags=globalVars['tags'])
az1_pubsubnet.create_tags  (Tags=globalVars['tags'])
az1_sparesubnet.create_tags(Tags=globalVars['tags'])
az2_pvtsubnet.create_tags  (Tags=globalVars['tags'])
az2_pubsubnet.create_tags  (Tags=globalVars['tags'])
az2_sparesubnet.create_tags(Tags=globalVars['tags'])
intGateway.create_tags     (Tags=globalVars['tags'])
routeTable.create_tags     (Tags=globalVars['tags'])

vpc.create_tags            (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-vpc'}])
az1_pvtsubnet.create_tags  (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az1-private-subnet'}])
az1_pubsubnet.create_tags  (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az1-public-subnet'}])
az1_sparesubnet.create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az1-spare-subnet'}])
az2_pvtsubnet.create_tags  (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az2-private-subnet'}])
az2_pubsubnet.create_tags  (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az2-public-subnet'}])
az2_sparesubnet.create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-az2-spare-subnet'}])
intGateway.create_tags     (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-igw'}])
routeTable.create_tags     (Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-rtb'}])

# Let create the Public & Private Security Groups
elbSecGrp = ec2.create_security_group(DryRun=False,
                                      GroupName='elbSecGrp',
                                      Description='ElasticLoadBalancer_Security_Group',
                                      VpcId=vpc.id
                                      )

pubSecGrp = ec2.create_security_group(DryRun=False,
                                      GroupName='pubSecGrp',
                                      Description='Public_Security_Group',
                                      VpcId=vpc.id
                                      )

pvtSecGrp = ec2.create_security_group(DryRun=False,
                                      GroupName='pvtSecGrp',
                                      Description='Private_Security_Group',
                                      VpcId=vpc.id
                                      )

elbSecGrp.create_tags(Tags=globalVars['tags'])
pubSecGrp.create_tags(Tags=globalVars['tags'])
pvtSecGrp.create_tags(Tags=globalVars['tags'])

elbSecGrp.create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-elb-security-group'}])
pubSecGrp.create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-public-security-group'}])
pvtSecGrp.create_tags(Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-private-security-group'}])

# Add a rule that allows inbound SSH, HTTP, HTTPS traffic ( from any source )
ec2Client.authorize_security_group_ingress(GroupId=elbSecGrp.id,
                                           IpProtocol='tcp',
                                           FromPort=8000,
                                           ToPort=8000,
                                           CidrIp='0.0.0.0/0'
                                           )

# Allow Public Security Group to receive traffic from ELB Security group
ec2Client.authorize_security_group_ingress(GroupId=pubSecGrp.id,
                                           IpPermissions=[{'IpProtocol': 'tcp',
                                                           'FromPort': 8000,
                                                           'ToPort': 8000,
                                                           'UserIdGroupPairs': [{'GroupId': elbSecGrp.id}]
                                                           }]
                                           )

# Allow Private Security Group to receive traffic from Application Security group
ec2Client.authorize_security_group_ingress(GroupId=pvtSecGrp.id,
                                           IpPermissions=[{'IpProtocol': 'tcp',
                                                           'FromPort': 5432,
                                                           'ToPort': 5432,
                                                           'UserIdGroupPairs': [{'GroupId': pubSecGrp.id}]
                                                           }]
                                           )

ec2Client.authorize_security_group_ingress(GroupId=pvtSecGrp.id,
                                           IpPermissions=[{'IpProtocol': 'tcp',
                                                           'FromPort': 8000,
                                                           'ToPort': 8000,
                                                           'UserIdGroupPairs': [{'GroupId': pubSecGrp.id}]
                                                           }]
                                           )

# Allow Private Security Group to receive traffic from Application Public group
ec2Client.authorize_security_group_ingress(GroupId=pubSecGrp.id,
                                           IpProtocol='tcp',
                                           FromPort=8000,
                                           ToPort=8000,
                                           CidrIp='0.0.0.0/0'
                                           )
ec2Client.authorize_security_group_ingress(GroupId=pubSecGrp.id,
                                           IpProtocol='tcp',
                                           FromPort=443,
                                           ToPort=443,
                                           CidrIp='0.0.0.0/0'
                                           )
ec2Client.authorize_security_group_ingress(GroupId=pubSecGrp.id,
                                           IpProtocol='tcp',
                                           FromPort=22,
                                           ToPort=22,
                                           CidrIp='0.0.0.0/0'
                                           )

# Creation of bucket on S3 
bucket_name = globalVars['Project']['Value'] + '-s3bucket-' + globalVars['env']['Value'] 
print('Creating new bucket with name: {}'.format(bucket_name))

response = client.create_bucket(
    ACL='private',
    Bucket=bucket_name,
    CreateBucketConfiguration={
       'LocationConstraint': globalVars['REGION_NAME']
})

# Retrieve the list of existing buckets
response = s3.list_buckets()

# Output the bucket names
print('Existing buckets:')
for bucket in response['Buckets']:
    print(f'  {bucket["Name"]}')

#Key-pair creation 

customEC2Keys = ec2Client.describe_key_pairs()['KeyPairs']
if not next((key for key in customEC2Keys if key["KeyName"] == globalVars['EC2-KeyName']), False):
    ec2_key_pair = ec2.create_key_pair(KeyName=globalVars['EC2-KeyName'])
    print("New Private Key created,Save the below key-material\n\n")
    print(ec2_key_pair.key_material)

#User data script for instances 

userDataCode = """
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
sudo docker-compose up -d 
sudo ./gradlew run
"""

# Create the Public App Test Instance
instanceLst = ec2.create_instances(ImageId=globalVars['EC2-Amazon-AMI-ID'],
                                   MinCount=1,
                                   MaxCount=2,
                                   KeyName=globalVars['EC2-KeyName'],
                                   UserData=userDataCode,
                                   InstanceType=globalVars['EC2-InstanceType'],                             
                                   NetworkInterfaces=[
                                       {
                                           'SubnetId': az1_pubsubnet.id,
                                           'Groups': [pubSecGrp.id],
                                           'DeviceIndex': 0,
                                           'DeleteOnTermination': True,
                                           'AssociatePublicIpAddress': True,
                                       }
                                   ],
                                   )
#Creating lunch configuration 
asgLaunchConfig = asgClient.create_launch_configuration(
    LaunchConfigurationName=globalVars['ASG-LaunchConfigName'],
    ImageId=globalVars['EC2-Amazon-AMI-ID'],
    KeyName=globalVars['EC2-KeyName'],
    SecurityGroups=[pubSecGrp.id],
    UserData=userDataCode,
    InstanceType=globalVars['EC2-InstanceType'],
    InstanceMonitoring={'Enabled': False },
    EbsOptimized=False,
    AssociatePublicIpAddress=False
)

# create Auto-Scaling Group
ASGSubnets = az1_pubsubnet.id + "," +az2_pubsubnet.id
asGroup=asgClient.create_auto_scaling_group(
    AutoScalingGroupName=globalVars['ASG-AutoScalingGroupName'],
    LaunchConfigurationName=globalVars['ASG-LaunchConfigName'],
    MinSize=1,
    MaxSize=3,
    DesiredCapacity=2,
    DefaultCooldown=120,
    HealthCheckType='EC2',
    HealthCheckGracePeriod=60,
    Tags=globalVars['tags'],
    VPCZoneIdentifier=ASGSubnets
    )

#Tagging instances 
asgClient.create_or_update_tags(
    Tags=[
        {
            'ResourceId': globalVars['ASG-AutoScalingGroupName'],
            'ResourceType': 'auto-scaling-group',
            'Key': 'Name',
            'Value': globalVars['Project']['Value'] + '-ASG-Group',
            'PropagateAtLaunch': True
        },
    ]
)

## First lets create the RDS Subnet Groups
rdsDBSubnetGrp = rds.create_db_subnet_group(DBSubnetGroupName=globalVars['RDS-DBSubnetGroup'],
                                            DBSubnetGroupDescription=globalVars['RDS-DBSubnetGroup'],
                                            SubnetIds=[az1_pvtsubnet.id, az2_pvtsubnet.id],
                                            Tags=[{'Key': 'Name',
                                                   'Value': globalVars['Project']['Value'] + '-DB-Subnet-Group'}]
                                            )

rdsInstance = rds.create_db_instance(DBInstanceIdentifier=globalVars['RDS-DBIdentifier'],
                       AllocatedStorage=5,
                       DBName=globalVars['RDS-DBName'],
                       Engine=globalVars['RDS-Engine'],
                       Port=5432,
                       StorageType='gp2',
                       StorageEncrypted=False,
                       AutoMinorVersionUpgrade=False,
                       MultiAZ=True,
                       MasterUsername=globalVars['RDS-DBMasterUserName'],
                       MasterUserPassword=globalVars['RDS-DBMasterUserPass'],
                       DBInstanceClass=globalVars['RDS-DBInstanceClass'],
                       VpcSecurityGroupIds=[pvtSecGrp.id],
                       DBSubnetGroupName=globalVars['RDS-DBSubnetGroup'],
                       CopyTagsToSnapshot=True,
                       Tags=[{'Key': 'Name', 'Value': globalVars['Project']['Value'] + '-RDS-Instance'}])

#Verifiy DB RDS creation 
waiter = rds.get_waiter('db_instance_available')
waiter.wait(DBInstanceIdentifier=globalVars['RDS-DBIdentifier'])

resp = rds.describe_db_instances(DBInstanceIdentifier= globalVars['RDS-DBIdentifier'])
db_instances = resp['DBInstances']
if len(db_instances) != 1:
    raise Exception('This should not have happened')
db_instance = db_instances[0]
status = db_instance['DBInstanceStatus']
if status == 'available':
    rdsEndpointDict = db_instance['Endpoint']
    globalVars['Endpoint'] = rdsEndpointDict['Address']

#List instances
ec2client = boto3.client('ec2')
response = ec2client.describe_instances()
for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:
        print(instance)
        print(instance["InstanceId"])

#Listing resources created. 
print("VPC ID                    : {0}".format(vpc.id))
print("AZ1 Public Subnet ID      : {0}".format(az1_pubsubnet.id))
print("AZ1 Private Subnet ID     : {0}".format(az1_pvtsubnet.id))
print("AZ1 Spare Subnet ID       : {0}".format(az1_sparesubnet.id))
print("Internet Gateway ID       : {0}".format(intGateway.id))
print("Route Table ID            : {0}".format(routeTable.id))
print("Public Security Group ID  : {0}".format(pubSecGrp.id))
print("Private Security Group ID : {0}".format(pvtSecGrp.id))
print("EC2 Key Pair              : {0}".format(globalVars['EC2-KeyName']))
print("EC2 PublicIP              : {0}".format(globalVars['EC2-KeyName']))
print("RDS Endpoint              : {0}".format(globalVars['Endpoint']))
###### Print to Screen ########