# MapCampaigner

MapCampaigner is aimed at managing and monitoring field data collection campaigns in OpenStreetMap. Campaign managers may use this tool to setup new and review ongoing and completed campaigns. Mappers can find nearby field campaigns to participate in. The result – improved data collection standards and project management.

Join the development:

  * Add to the discussion in the [issue tracker](https://github.com/hotosm/MapCampaigner/issues). Tag issues as Discussion or Ideas to contribute.
  * More information and project documentation about the vision and scope in the [wiki](https://github.com/hotosm/MapCampaigner/wiki)
  * Join online chat on [HOT’s Slack community](https://slack.hotosm.org/), #mapcampaigner channel.

## Project Overview

This project is based on the original work done in the osm-reporter. The project was extended to include a campaign management application. The aim of the campaign management is to allow field campaigns to be tracked and their quality measured.

### OSM Users

The OSM user identity is used in this project. All actions are performed as such. A list of authorized admin users is maintained in the settings file.

### How to install MapCampaigner locally

1. Fork this repo into your github account.
2. Clone the repo (from your github account).
3. Create a OpenStreetMap account

    [Sign Up | OpenStreetMap](https://www.openstreetmap.org/user/new)

    1. Go to My Settings > oauth settings > Register your application
    2. Name: my-mapcampaigner-local
    3. Main Application URL: http://localhost:5000
    4. Permissions: read their users preferences
    5. Keep the consumer key (OAUTH_CONSUMER_KEY) and secret (OAUTH_SECRET) somewhere, you'll need them later.
4. Create an AWS account

    [AWS Console - Signup](https://portal.aws.amazon.com/billing/signup#/start)

5. Create a S3 bucket in whatever region you like
    1. Must be a public bucket.
    2. Edit CORS configuration:

            <?xml version="1.0" encoding="UTF-8"?>
            <CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
            <CORSRule>
                <AllowedOrigin>*</AllowedOrigin>
                <AllowedMethod>GET</AllowedMethod>
                <AllowedMethod>HEAD</AllowedMethod>
                <MaxAgeSeconds>3000</MaxAgeSeconds>
                <AllowedHeader>Authorization</AllowedHeader>
            </CORSRule>
            </CORSConfiguration>

    4. Upload folders (in bucket) "surveys", "campaigns" and "thumbnail" at the root of your project. Your S3 structure should look like:

            campaigns/
            surveys/
            	buildings
            	...
            thumbnail/

6. Get your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY: Go to your AWS account > My Security Credentials > Access keys
7. Create a file on your machine ~/.aws/credentials

        [default]
        aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID
        aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY
        region=YOUR_REGION

8. Create a virtualenv:

        $> virtualenv venv
        $> source venv/bin/activate

9. Install requirements:

        $> pip install -r requirements.txt

10. Go to the AWS Console > IAM console > Create a policy

        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Stmt1464440182000",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "lambda:InvokeAsync",
                        "lambda:InvokeFunction"
                    ],
                    "Resource": [
                        "arn:aws:logs:*:*:*",
                        "*"
                    ]
                }
            ]
        }

11. Stay in the IAM console > Create a Role
    1. Service that will use this role: Lambda
    2. Policies:
        1. the one you just created
        2. AmazonS3FullAccess
        3. AWSLambdaFullAccess
        4. AWSLambdaRole
    3. Role name: whatever name you like
    4. Role description: role to execute MapCampaigner lambda functions
    5. Keep the role ARN (arn:aws:iam:::.....)

12. Create a file: `.env` in the project root with the following:

        # Project Config
        ENV=local
        PYTHONPATH=flask_project
        DEVELOPMENT=True
        DEBUG=True
        # TESTING=True
        DATA_FOLDER=/home/web/field-campaigner-data
        CSRF_ENABLED=True
        # AWS Config
        SECRET_KEY=<secret key from step 6>
        AWS_BUCKET=<AWS bucket name from step 5>
        AWS_REGION=<AWS region name from step 5>
        AWS_ROLE=<AWS role in arn format from step 11>
        # OpenStreetMap Config
        OAUTH_CONSUMER_KEY=<Oauth consumer key from step 3>
        OAUTH_SECRET=<Oauth secret from step 3>
        _OSMCHA_DOMAIN=https://osmcha.mapbox.com/
        OSMCHA_API_PATH=api/v1/
        OSMCHA_FRONTEND_URL=https://osmcha.mapbox.com/


13. Download and install Docker
14. Deploy the lambda functions

        $> python ./.travis/deploy_lambda_functions.py

15. Run the server:

        $> python flask_project/runserver.py

16. Open your browser and visit localhost:5000
17. Log in
    1. It should open an OpenStreetMap popup
    2. If not, then you didn't set up properly OAUTH_CONSUMER_KEY and OAUTH_SECRET
18. Create a campaign

### User Interface

#### Starting a Campaign

Authorized users may start a campaign. This is done by selecting the “Add Campaign” button on the Landing Page.

A campaign has standard attributes, such as boundaries, start and end dates as well as name and description. The campaign progress is obtained through insights functions, which are broken up into classes. These insights functions take data from a data source, such as the OSM reporter, and convert them to quantifiable insights. The campaign manager selects which insights functions best meet the requirements of this campaign.

#### Viewing a Campaign

The Campaign Dashboard Page shows the default attributes as well as the UI component of the Insights Function. Alongside the UI component each of the insights functions provide additional details on how these insights where obtained. These additional details may are shown if the user explodes the hyperlink with this information.

#### Editing a Campaign

A campaign is edited in the same view as it is created. As such this is not a very different experience.

## Technical Details

The insights functions are clearly understandable english sentences, which highlight an analytical goal. Some additional parameters may be given, but this is made clear when selecting this function. Under the hood there are two parts to this the first is the Data Provider, against which an Insights Function can be registered and the Insights Function itself.

### Data Provider

The Data Provider is an abstraction around the data source. External resource querying is handled here. The prime example is the OSM Reporter Function Provider, which provides the feature list over a given time period for a specific area. This data is aggregated here and passed on to the relevant insights functions.

### Insights Function

The Insights Function takes data from a Data Provider and performs a calculation over this data. The output of this function is a UI component, for displaying on the dashboard, a detailed description of how this data was obtained and, where relevant, a set of links on where to view/correct these.

## License

See LICENSE.md file.

## Contributors

Built by [Kartoza](http://kartoza.com/):

@cchristelis
@ann26
@meomancer
@dimasciput
@MariaSolovyeva
@pierrealixt

Based on previous osm-reporter work by:

Tim Sutton - tim@linfiniti.com
Yohan Boniface - yb@enix.org
Sun Ning - sunng@about.me
