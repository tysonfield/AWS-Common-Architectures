from constructs import Construct
from aws_cdk import (
	Stack,
	aws_ec2 as ec2,
	aws_rds as rds
	)

class privateNaclCidr(ec2.AclCidr):
	def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
		super().__init__()
		self.acl_cidr_config = kwargs
	def to_cidr_config(self):
		return self.acl_cidr_config

class CdkStack(Stack):
	def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)
		
		current_ami = ec2.MachineImage.latest_amazon_linux()

		vpc = ec2.Vpc(self, "vpc", 
			cidr = "10.0.0.0/16",
			subnet_configuration = [ec2.SubnetConfiguration(
				name = "private_subnet_isolated",
				subnet_type = ec2.SubnetType.PRIVATE_ISOLATED,
				cidr_mask = 24
			),
			ec2.SubnetConfiguration(
				name = "public_subnet",
				subnet_type = ec2.SubnetType.PUBLIC,
				cidr_mask = 24
			)],
			max_azs = 2
			)
		
		nacl_public = ec2.NetworkAcl(self, "nacl_public",
			vpc = vpc,
			network_acl_name = "nacl_public",
			subnet_selection = ec2.SubnetSelection(subnets = vpc.select_subnets(subnet_type = ec2.SubnetType.PUBLIC).subnets)
		)

		nacl_private = ec2.NetworkAcl(self, "nacl_private",
			vpc = vpc,
			network_acl_name = "nacl_private",
			subnet_selection = ec2.SubnetSelection(subnets = vpc.select_subnets(subnet_type = ec2.SubnetType.PRIVATE_ISOLATED).subnets)
		)

		nacl_private_cidr = privateNaclCidr(self, "nacl_private_cidr",
			cidrBlock = '10.0.0.0/16')

		nacl_private.add_entry("nacl_private_allow_http_all",
			cidr = nacl_private_cidr,
			rule_number = 100,
			traffic = ec2.AclTraffic.tcp_port(80),
			direction = ec2.TrafficDirection.INGRESS,
			rule_action = ec2.Action.ALLOW
		)

		web_security_group = ec2.SecurityGroup(self, "web_security_group",
			vpc = vpc,
			allow_all_outbound = False
			)
		
		app_security_group = ec2.SecurityGroup(self, "app_security_group",
			vpc = vpc,
			allow_all_outbound = False
			)
		
		db_security_group = ec2.SecurityGroup(self, "db_security_group",
			vpc = vpc,
			allow_all_outbound = False
			)
		
		web_instance = ec2.Instance(self, "web_instance",
			instance_type = ec2.InstanceType("t2.micro"),
			machine_image = current_ami,
			vpc = vpc,
			security_group = web_security_group,
			vpc_subnets = ec2.SubnetSelection(subnets = vpc.select_subnets(subnet_type = ec2.SubnetType.PUBLIC).subnets),
			key_name = "web-instance"
			)

		app_instance = ec2.Instance(self, "app_instance",
			instance_type = ec2.InstanceType("t2.micro"),
			machine_image = current_ami,
			vpc = vpc,
			security_group = app_security_group,
			vpc_subnets = ec2.SubnetSelection(subnets = vpc.select_subnets(subnet_type = ec2.SubnetType.PRIVATE_ISOLATED).subnets),
			key_name = "app-instance"
			)	

		db_instance = rds.DatabaseInstance(self, "db_instance",
			engine = rds.DatabaseInstanceEngine.mysql(version = rds.MysqlEngineVersion.VER_8_0),
			vpc = vpc,
			allocated_storage = 20,
			database_name = "db",
			instance_identifier = "db-instance",
			instance_type = ec2.InstanceType("t2.micro"),
			security_groups = [db_security_group],
			storage_encrypted = False,
			vpc_subnets = ec2.SubnetSelection(subnets = vpc.select_subnets(subnet_type = ec2.SubnetType.PRIVATE_ISOLATED).subnets)
			)

		app_instance.connections.allow_from(web_instance, ec2.Port.tcp(22))
		web_instance.connections.allow_to(app_instance, ec2.Port.tcp(22))
		app_instance.connections.allow_from(web_instance, ec2.Port.tcp(80))
		web_instance.connections.allow_to(app_instance, ec2.Port.tcp(80))
		db_instance.connections.allow_from(app_instance, ec2.Port.tcp(3306))
		app_instance.connections.allow_to(db_instance, ec2.Port.tcp(3306))
