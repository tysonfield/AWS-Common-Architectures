from constructs import Construct
from aws_cdk import (
	Stack,
	aws_ec2 as ec2
	)

class CdkStack(Stack):
	def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)
		
		current_ami = ec2.MachineImage.latest_amazon_linux()

		vpc = ec2.Vpc(self, "test_vpc", 
			cidr = "10.0.0.0/16",
			subnet_configuration = [ec2.SubnetConfiguration(
				name = "test_subnet_private",
				subnet_type = ec2.SubnetType.PRIVATE_WITH_NAT,
				cidr_mask = 24
			),
			ec2.SubnetConfiguration(
				name = "test_subnet_public",
				subnet_type = ec2.SubnetType.PUBLIC,
				cidr_mask = 24
			)],
			max_azs = 1
			)
		
		security_group_public = ec2.SecurityGroup(self, "test_security_group_public",
			vpc = vpc,
			allow_all_outbound = False
			)
		
		security_group_public.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22))
		
		public_instance = ec2.Instance(self, "test_instance_public",
			instance_type = ec2.InstanceType("t2.micro"),
			machine_image = current_ami,
			vpc = vpc,
			security_group = security_group_public,
			vpc_subnets = ec2.SubnetSelection(subnets = vpc.select_subnets(subnet_type = ec2.SubnetType.PUBLIC).subnets),
			key_name = "test-instance-public"
			)

		security_group_private = ec2.SecurityGroup(self, "test_security_group_private",
			vpc = vpc,
			allow_all_outbound = False
			)

		private_instance = ec2.Instance(self, "test_instance_private",
			instance_type = ec2.InstanceType("t2.micro"),
			machine_image = current_ami,
			vpc = vpc,
			security_group = security_group_private,
			vpc_subnets = ec2.SubnetSelection(subnets = vpc.select_subnets(subnet_type = ec2.SubnetType.PRIVATE_WITH_NAT).subnets),
			key_name = "test-instance-private"
			)
			