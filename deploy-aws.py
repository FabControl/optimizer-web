import boto3
import sys
import os
from time import sleep
from functools import partial
import re
import subprocess


class Env:
    def __init__(self):
        for k, v in os.environ.items():
            setattr(self, k, v)

        self.source = sys.argv[1]
        self.deploymentMatcher = partial(re.match, sys.argv[2])

        self.bucketKey = '/'.join((self.BITBUCKET_BRANCH, self.BITBUCKET_COMMIT))
        self.versionName = '-'.join((self.BITBUCKET_BRANCH, self.BITBUCKET_COMMIT))


def log(s):
    sys.stdout.write(s)
    sys.stdout.flush()


env = Env()
# upload compressed source to s3
log('Uploading "{0.source}" ({1} bytes) to s3 {0.BUCKET}/{0.bucketKey}...'.format(
            env, os.path.getsize(env.source)))
s3 = boto3.client('s3')
with open(env.source, 'rb') as f:
    s3.upload_fileobj(f, env.BUCKET, env.bucketKey)

log('Done!\n')

# create beanstalk version
log('Creating app version {0.versionName} for {0.BEANSTALK_APP}...'.format(env))
beanstalk = boto3.client('elasticbeanstalk')
r = beanstalk.create_application_version(
            ApplicationName=env.BEANSTALK_APP,
            VersionLabel=env.versionName,
            SourceBundle={
                'S3Bucket': env.BUCKET,
                'S3Key': env.bucketKey
                },
            Process=True
        )['ApplicationVersion']

sleep(0.2)
while r['Status'].upper() == 'PROCESSING':
    log('\nProcessing...')
    sleep(0.5)
    r = beanstalk.describe_application_versions(
                ApplicationName=env.BEANSTALK_APP,
                VersionLabels=[env.versionName]
            )['ApplicationVersions'][0]

if r['Status'].upper() != 'PROCESSED':
    raise Exception('Processing failed!')
log('Done!\n')

# Update selected deployments
deployments = [ x['EnvironmentName'] for x in
                    beanstalk.describe_environments(
                            ApplicationName=env.BEANSTALK_APP,
                            IncludeDeleted=False
                        )['Environments']
                ]
for d in filter(env.deploymentMatcher, deployments):
    log('Updating "{0}"...'.format(d))
    beanstalk.update_environment(
            ApplicationName=env.BEANSTALK_APP,
            EnvironmentName=d,
            VersionLabel=env.versionName
            )
    log('Update started!\n')

    sleep(0.2)

# Clean up previous versions
log('Removing old versions\n')
versions = filter(lambda x: re.match(env.BITBUCKET_BRANCH, x['VersionLabel']),
                beanstalk.describe_application_versions(
                            ApplicationName=env.BEANSTALK_APP
                    )['ApplicationVersions']
                )

versions = [ v['VersionLabel'] for v in sorted(versions, key=lambda x: x.get('DateUpdated')) ]

while len(versions) > int(env.KEEP_VERSION_RELEASES):
    v = versions.pop(0)
    log('Removing "{0}" ...'.format(v))
    beanstalk.delete_application_version(
            ApplicationName=env.BEANSTALK_APP,
            VersionLabel=v,
            DeleteSourceBundle=True
        )
    sleep(0.2)
    log('Removed!\n')

log('Completed successfully!\n')
