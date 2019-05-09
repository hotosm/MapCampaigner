import os
import re
import subprocess

CONFIG = {
    'local': {
        'env': {
            's3_bucket': 'fieldcampaigner-data',
            'env': 'local'
        },
        'role': 'arn:aws:iam::142767531394:role/lambda_field_campaigner'
    },
    'staging': {
        'env': {
            's3_bucket': 'hotosm-fieldcampaigner-data-staging',
            'env': 'staging'
        },
        'role': 'arn:aws:iam::670261699094:role/lambda_mapcampaigner'
    },
    'production': {
        'env': {
            's3_bucket': 'hotosm-fieldcampaigner-data-production',
            'env': 'production'
        },
        'role': 'arn:aws:iam::670261699094:role/lambda_mapcampaigner'
    }
}


def install_dependencies(path):
    requirements_path = '{path}/requirements.txt'.format(
        path=path)
    package_json_path = '{path}/package.json'.format(
        path=path)
    dependencies_path = '{path}/dependencies'.format(
        path=path)
    modules_path = '{path}/node_modules'.format(
        path=path)

    if os.path.isfile(requirements_path):
        if os.path.exists(dependencies_path):
            os.system('rm -rf {dependencies_path}'.format(
                dependencies_path=dependencies_path))

        os.system('mkdir -p {dependencies_path}'.format(
            dependencies_path=dependencies_path))

        os.system('touch {dependencies_path}/__init__.py'.format(
            dependencies_path=dependencies_path))

        command = ' '.join([
            'docker run -it',
            '-v `pwd`/{dependencies_path}:/dependencies',
            '-v `pwd`/{requirements_path}:/requirements.txt',
            'install-aws-dependencies']).format(
                dependencies_path=dependencies_path,
                requirements_path=requirements_path)
        os.system(command)
    if os.path.isfile(package_json_path):
        if os.path.exists(modules_path):
            os.system('rm -rf {modules_path}'.format(
                modules_path=modules_path))

        os.system('mkdir -p {modules_path}'.format(
            modules_path=modules_path))

        command = ' '.join([
            'docker run -it',
            '-v `pwd`/{modules_path}:/node_modules',
            '-v `pwd`/{package_json_path}:/package.json',
            'install-aws-dependencies-nodejs']).format(
                modules_path=modules_path,
                package_json_path=package_json_path)
        os.system(command)


def zip_files(path, function_name):
    zip_path = '{path}/{function_name}.zip'.format(
        path=path,
        function_name=function_name)
    if os.path.isfile(zip_path):
        os.system('rm {zip_path}'.format(
            zip_path=zip_path))
    os.system('cd {path} && zip -X -r ./{function_name}.zip *'.format(
        path=path,
        function_name=function_name))
    return zip_path


def copy_zip_to_s3(zip_path, function_name):
    env = set_env_from_branch()
    command = ' '.join([
        'aws s3 cp {zip_path}',
        's3://{bucket}/lambda_zips/{function_name}.zip',
        '--profile mapcampaigner'
    ]).format(
        zip_path=zip_path,
        bucket=CONFIG[env]['env']['s3_bucket'],
        function_name=function_name)
    os.system(command)


def set_env_from_branch():
    branch = os.environ.get('TRAVIS_BRANCH', None)
    if branch == 'develop':
        return 'staging'
    elif branch == 'master':
        return 'production'
    else:
        return 'local'


def set_env_variables():
    env = set_env_from_branch()
    list_env_vars = list(map(lambda var:
        '{var_key}={var_value}'.format(
            var_key=var[0].upper(),
            var_value=var[1]
            ),
        CONFIG[env]['env'].items()
        ))
    return '"{s}{env_vars_to_str}{e}"'.format(
        s='{',
        env_vars_to_str=','.join(list_env_vars),
        e='}'
        )


def update_function(path, function_name):
    env = set_env_from_branch()
    install_dependencies(path)
    zip_path = zip_files(path, function_name)

    copy_zip_to_s3(zip_path, function_name)

    function_name_with_env = '{env}_{function_name}'.format(
        env=env,
        function_name=function_name)

    print('updating code to aws...')
    command = ' '.join([
        'aws lambda update-function-code',
        '--function-name {function_name_with_env}',
        '--s3-bucket {bucket}',
        '--s3-key lambda_zips/{function_name}.zip',
        '--profile mapcampaigner'
    ]).format(
        function_name_with_env=function_name_with_env,
        function_name=function_name,
        bucket=CONFIG[env]['env']['s3_bucket'])

    os.system(command)
    print('done.')
    print('updating configuration to aws...')
    command = ' '.join([
        'aws lambda update-function-configuration',
        '--function-name {function_name}',
        '--environment Variables={env_variables}',
        '--timeout 300',
        '--memory-size 512',
        '--profile mapcampaigner'
    ]).format(
        function_name=function_name_with_env,
        env_variables=set_env_variables())

    os.system(command)
    print('done.')


def create_function(path, function_name):
    install_dependencies(path)
    env = set_env_from_branch()
    zip_path = zip_files(path, function_name)
    role = CONFIG[set_env_from_branch()]['role']

    copy_zip_to_s3(zip_path, function_name)

    function_name_with_env = '{env}_{function_name}'.format(
        env=set_env_from_branch(),
        function_name=function_name)
    code = 'S3Bucket={bucket},S3Key=lambda_zips/{function_name}.zip'.format(
        bucket=CONFIG[env]['env']['s3_bucket'],
        function_name=function_name)

    command = ' '.join([
        'aws lambda create-function',
        '--region us-west-2',
        '--function-name {function_name_with_env}',
        '--runtime python3.6',
        '--role {role}',
        '--handler lambda_function.lambda_handler',
        '--environment Variables={env_variables}',
        '--code {code}',
        '--memory-size 512',
        '--timeout 300',
        '--profile mapcampaigner'
    ]).format(
        function_name=function_name,
        function_name_with_env=function_name_with_env,
        role=role,
        env_variables=set_env_variables(),
        code=code)
    os.system(command)


def get_lambda_functions_on_aws():
    p = subprocess.Popen(
        'aws lambda list-functions --profile mapcampaigner',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
        )

    lambda_functions_on_aws = []
    for line in p.stdout.readlines():
        line = line.decode("utf-8").strip()
        results = re.search(
            "\"(FunctionName)\": \"([a-zA-Z_]+)\",",
            line.strip()
            )
        if results:
            lambda_functions_on_aws.append(results.group(2))
    return lambda_functions_on_aws


def deploy():
    env = set_env_from_branch()
    lambda_functions_on_aws = get_lambda_functions_on_aws()
    for function_group in ['compute', 'download', 'process', 'render']:
        path = 'lambda_functions/{}'.format(function_group)
        if os.path.exists(path):
            for function in os.listdir(path):
                function_path = '{path}/{function}'.format(
                    path=path,
                    function=function)
                if (
                    os.path.isfile(
                        '{path}/lambda_function.py'.format(path=function_path)
                    ) or os.path.isfile(
                        '{path}/index.js'.format(path=function_path)
                    )
                ):
                    function_name = '{function_group}_{function}'.format(
                        function_group=function_group,
                        function=function)
                    function_name_with_env = '{env}_{function_name}'.format(
                        env=env,
                        function_name=function_name)

                    if function_name_with_env in lambda_functions_on_aws:
                        update_function(function_path, function_name)
                    else:
                        create_function(function_path, function_name)


def deploy_function(function_group, function):
    env = set_env_from_branch()
    lambda_functions_on_aws = get_lambda_functions_on_aws()
    if os.path.exists('lambda_functions/{}'.format(function_group)):
        if (
            os.path.isfile(
                'lambda_functions/{}/{}/lambda_function.py'.format(
                    function_group, function
                )
            ) or os.path.isfile(
                'lambda_functions/{}/{}/index.js'.format(
                    function_group, function
                )
            )
        ):
            function_path = 'lambda_functions/{}/{}'.format(
                function_group,
                function)
            function_name = '{function_group}_{function}'.format(
                function_group=function_group,
                function=function)
            function_name_with_env = '{env}_{function_name}'.format(
                env=env,
                function_name=function_name)

            if function_name_with_env in lambda_functions_on_aws:
                update_function(function_path, function_name)
            else:
                create_function(function_path, function_name)


def build_docker_container():
    command = ' '.join([
        'docker build',
        '-t install-aws-dependencies',
        '-f .travis/Dockerfile .'])
    os.system(command)


def build_nodejs_docker_container():
    command = ' '.join([
        'docker build',
        '-t install-aws-dependencies-nodejs',
        '-f .travis/Dockerfile .'])
    os.system(command)


def main():
    import sys
    argc = len(sys.argv)
    build_docker_container()
    build_nodejs_docker_container()
    if argc == 1:
        deploy()
    elif argc == 4:
        if sys.argv[1] == 'deploy':
            deploy_function(
                function_group=sys.argv[2],
                function=sys.argv[3])
        elif sys.argv[1] == 'install':
            function_path = \
                'lambda_functions/{function_group}/{function}'.format(
                    function_group=sys.argv[2],
                    function=sys.argv[3])
            install_dependencies(function_path)


if __name__ == "__main__":
    main()
