TRACK = dict(
    id="aws",
    title="AWS for Engineers",
    icon="☁️",
    color="#ff9900",
    group="Cloud & DevOps",
    blurb="Amazon Web Services from zero: accounts and billing, EC2, S3, VPC networking, databases, IAM and "
          "security, monitoring, DNS and content delivery, load balancing, auto scaling, queues, serverless, "
          "containers, infrastructure as code, the Well-Architected pillars, AWS for ML and data, a worked "
          "project from one server to a multi-AZ production design, and Solutions Architect exam practice.",
    sources=[
        "AWS Certified Solutions Architect Official Study Guide: Associate Exam (Sybex), ch. 1-14",
        "AWS documentation (docs.aws.amazon.com): EC2, EBS, S3, VPC, RDS, DynamoDB, IAM, Lambda, CloudWatch, "
        "Route 53, CloudFront, Elastic Load Balancing, Auto Scaling, SQS, SNS, Kinesis, CloudFormation user guides",
        "AWS Well-Architected Framework (docs.aws.amazon.com/wellarchitected)",
        "AWS Billing user guide: Free Tier (docs.aws.amazon.com/awsaccountbilling)",
        "Amazon Lightsail, Amazon SageMaker AI and Amazon Bedrock user guides (docs.aws.amazon.com)",
        "AWS Certified Solutions Architect - Associate (SAA-C03) exam guide (docs.aws.amazon.com/aws-certification)",
    ],
    modules=[
        dict(
            id="cloud-zero",
            title="1. The cloud from zero",
            summary="What cloud computing is, Regions and Availability Zones, shared responsibility, the four "
                    "ways to drive AWS, and a safe first account with MFA and budgets.",
            lessons=[
                dict(id="what-is-cloud", title="What cloud computing is, and the AWS global map", file="01-what-is-cloud.md"),
                dict(id="responsibility-and-tools", title="Shared responsibility and four ways to drive AWS", file="02-shared-responsibility-tools.md"),
                dict(id="account-and-billing", title="A safe first account: root user, MFA, budgets and the free tier", file="03-account-billing.md"),
            ],
            problems=["aws-tag-compliance", "aws-bill-estimator"],
        ),
        dict(
            id="ec2",
            title="2. EC2 and block storage",
            summary="Virtual servers: instance types, AMIs, user data, purchasing options, placement groups, "
                    "EBS volume types, snapshots and instance store.",
            lessons=[
                dict(id="ec2-instances", title="EC2 instances, instance types, AMIs and user data", file="04-ec2-instances.md"),
                dict(id="ec2-purchasing", title="Paying for EC2: purchasing options, placement groups and right-sizing", file="05-ec2-purchasing.md"),
                dict(id="ebs-storage", title="EBS volumes, snapshots and instance store", file="06-ebs-storage.md"),
            ],
            problems=["aws-ec2-purchase-cost", "aws-right-size", "aws-ebs-performance"],
        ),
        dict(
            id="storage",
            title="3. S3, Glacier, EFS and FSx",
            summary="Object storage end to end: buckets, storage classes, lifecycle, versioning, encryption, "
                    "replication, presigned URLs and static hosting, then shared file systems.",
            lessons=[
                dict(id="s3-basics", title="S3 buckets, objects, storage classes and lifecycle rules", file="07-s3-basics.md"),
                dict(id="s3-protection", title="S3 versioning, encryption, replication, access control and presigned URLs", file="08-s3-advanced.md"),
                dict(id="file-storage", title="EFS, FSx and Storage Gateway: choosing block, file or object", file="09-file-storage.md"),
            ],
            problems=["aws-s3-lifecycle-schedule", "aws-s3-storage-cost", "aws-presigned-url-check", "aws-bucket-public-detector"],
        ),
        dict(
            id="vpc",
            title="4. VPC networking",
            summary="Private networks in the cloud: CIDR planning, subnets, route tables, gateways, security "
                    "groups and network ACLs, peering, Transit Gateway, endpoints, VPN and Direct Connect.",
            lessons=[
                dict(id="vpc-basics", title="VPCs, CIDR planning, subnets, route tables and gateways", file="10-vpc-basics.md"),
                dict(id="vpc-firewalls", title="Security groups versus network ACLs", file="11-vpc-security.md"),
                dict(id="vpc-connectivity", title="Connecting networks: peering, Transit Gateway, endpoints, VPN and Direct Connect", file="12-vpc-connectivity.md"),
            ],
            problems=["aws-subnet-public-private", "aws-route-longest-prefix", "aws-vpc-subnet-planner", "aws-sg-nacl-evaluate"],
        ),
        dict(
            id="databases",
            title="5. Databases",
            summary="RDS engines, Multi-AZ, read replicas and backups, Aurora, DynamoDB keys, indexes and "
                    "capacity, plus ElastiCache, DAX and Redshift.",
            lessons=[
                dict(id="rds-aurora", title="RDS and Aurora: managed relational databases", file="13-rds-aurora.md"),
                dict(id="dynamodb", title="DynamoDB: tables, keys, indexes, capacity and streams", file="14-dynamodb.md"),
                dict(id="cache-warehouse", title="ElastiCache, DAX and Redshift", file="15-cache-warehouse.md"),
            ],
            problems=["aws-dynamodb-capacity", "aws-gsi-projection", "aws-dynamodb-hot-partition",
                      "aws-dynamodb-query-scan", "aws-rds-failover-lag"],
        ),
        dict(
            id="security",
            title="6. IAM and security",
            summary="Users, groups, roles and policies, how a request is evaluated, STS, Organizations and "
                    "SCPs, KMS, Secrets Manager, CloudTrail, Config, GuardDuty, WAF and Shield.",
            lessons=[
                dict(id="iam-identities", title="IAM users, groups, roles and policies", file="16-iam-identities.md"),
                dict(id="iam-evaluation", title="Policy evaluation, STS, Organizations and SCPs", file="17-iam-evaluation.md"),
                dict(id="security-services", title="KMS, Secrets Manager and the detective and protective services", file="18-security-services.md"),
            ],
            problems=["aws-iam-least-privilege-audit", "aws-iam-evaluate"],
        ),
        dict(
            id="monitoring",
            title="7. Monitoring and observability",
            summary="CloudWatch metrics, logs and alarms, EventBridge rules and schedules, and X-Ray tracing.",
            lessons=[
                dict(id="cloudwatch", title="CloudWatch metrics, logs and alarms", file="19-cloudwatch.md"),
                dict(id="eventbridge-xray", title="EventBridge and X-Ray: reacting to events and tracing requests", file="20-eventbridge-xray.md"),
            ],
            problems=["aws-cloudwatch-alarm"],
        ),
        dict(
            id="dns-cdn",
            title="8. DNS and content delivery",
            summary="Route 53 record types and routing policies, CloudFront caching and Global Accelerator.",
            lessons=[
                dict(id="route53", title="DNS and Route 53: records and routing policies", file="21-route53.md"),
                dict(id="cloudfront", title="CloudFront and Global Accelerator", file="22-cloudfront.md"),
            ],
            problems=["aws-route53-resolve", "aws-cloudfront-cache"],
        ),
        dict(
            id="elasticity",
            title="9. Elasticity and decoupling",
            summary="Elastic Load Balancing, Auto Scaling policies, SQS queues, SNS topics, Kinesis streams and "
                    "Step Functions workflows.",
            lessons=[
                dict(id="load-balancing", title="Elastic Load Balancing: ALB, NLB and health checks", file="23-load-balancing.md"),
                dict(id="auto-scaling", title="EC2 Auto Scaling: groups, launch templates and scaling policies", file="24-auto-scaling.md"),
                dict(id="messaging", title="SQS and SNS: queues, topics and fan-out", file="25-messaging.md"),
                dict(id="streams-workflows", title="Kinesis, Step Functions and SWF", file="26-streams-workflows.md"),
            ],
            problems=["aws-health-check-state", "aws-alb-routing", "aws-asg-target-tracking", "aws-asg-step-scaling",
                      "aws-sns-filter-fanout", "aws-sqs-simulator", "aws-kinesis-shards"],
        ),
        dict(
            id="serverless-containers",
            title="10. Compute beyond EC2",
            summary="Lambda and API Gateway, containers on ECS, EKS and Fargate, Elastic Beanstalk and Batch.",
            lessons=[
                dict(id="lambda-apigw", title="Lambda and API Gateway: serverless compute", file="27-lambda-apigw.md"),
                dict(id="containers", title="Containers and platforms: ECS, EKS, Fargate, Elastic Beanstalk and Batch", file="28-containers.md"),
            ],
            problems=["aws-lambda-cost", "aws-lambda-concurrency"],
        ),
        dict(
            id="automation",
            title="11. Deployment and automation",
            summary="CloudFormation and the CDK, Systems Manager, and the CodePipeline family for CI/CD.",
            lessons=[
                dict(id="cloudformation-cdk", title="Infrastructure as code with CloudFormation and the CDK", file="29-cloudformation-cdk.md"),
                dict(id="ssm-codepipeline", title="Systems Manager and the CodePipeline family", file="30-ssm-codepipeline.md"),
            ],
            problems=[],
        ),
        dict(
            id="well-architected",
            title="12. The Well-Architected pillars",
            summary="Reliability, RTO and RPO, disaster-recovery strategies, performance efficiency, cost "
                    "optimisation, security in every layer and operational excellence.",
            lessons=[
                dict(id="reliability-dr", title="Reliability: resilient architectures, RTO, RPO and disaster recovery", file="31-reliability-dr.md"),
                dict(id="performance-cost", title="Performance efficiency and cost optimisation", file="32-performance-cost.md"),
                dict(id="security-opex", title="The security pillar, compliance and operational excellence", file="33-security-opex.md"),
            ],
            problems=["aws-dr-strategy"],
        ),
        dict(
            id="ml-data",
            title="13. AWS for ML and data",
            summary="S3 data lakes, Glue, Athena and EMR, then SageMaker, Bedrock, GPU instances and their cost.",
            lessons=[
                dict(id="data-lakes", title="Data lakes on S3: Glue, Athena, EMR and Firehose", file="34-data-lakes.md"),
                dict(id="sagemaker-bedrock", title="SageMaker, Bedrock and GPU instances", file="35-sagemaker-bedrock.md"),
            ],
            problems=["aws-spot-training-steps"],
        ),
        dict(
            id="project",
            title="14. Lightsail to production: a worked project",
            summary="Take a small web API from one server to a load-balanced, auto-scaled, multi-AZ design "
                    "with RDS, S3, CloudFront, CI/CD and monitoring.",
            lessons=[
                dict(id="project-foundations", title="Project part 1: from one Lightsail server to a VPC with RDS and S3", file="36-project-single.md"),
                dict(id="project-scale", title="Project part 2: load balancing, auto scaling, CloudFront, CI/CD and monitoring", file="37-project-scale.md"),
            ],
            problems=["aws-az-failure-capacity", "aws-rolling-deploy-plan"],
        ),
        dict(
            id="interview",
            title="15. AWS interview and certification essentials",
            summary="A method for design questions, the classic comparisons, exam strategy for the Solutions "
                    "Architect Associate and 60 practice scenarios with explained answers.",
            lessons=[
                dict(id="design-answers", title="Answering 'design X on AWS' and the classic comparisons", file="38-design-answers.md"),
                dict(id="exam-practice-1", title="Exam strategy and practice scenarios 1-30", file="39-exam-questions-1.md"),
                dict(id="exam-practice-2", title="Practice scenarios 31-60", file="40-exam-questions-2.md"),
            ],
            problems=["aws-composite-availability"],
        ),
    ],
)
