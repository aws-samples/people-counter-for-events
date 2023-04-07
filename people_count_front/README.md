# AWS VizCounter

## Overview

AWS VizCounter provide vue.js front page include total counter and currunt counter. </br>

## Pre-Requisites

-   The following hardware and AWS environment are recommended.

### AWS environment

-   An IAM user with administrator privileges
-   VizCounter's AWS backend resource, such ad Amazon Kinesis, AWS Lambda, Amazon DynamoDB or any oher resource. Please check [here](https://gitlab.aws.dev/vizcounter-dev/people_count)

### Hardware (PC for operation)

-   node.js (16 or higher)
-   npm (8.16.0 or higher)
-   AWS CLI (2.7.15 or higher)
-   python (3.9.11 or higher)
-   Browser (Chrome or Firefox)

```
If you use cloud9, you don't have to consider this.
```

## Project setup

1. Move project root directory.

```
cd <your path>/people_count_front
```

2. Please install npm pakage.

```
npm install
```

If you want show detail npm pakage, please see pacakge.json.

3. Run serve in your local environment.

```
npm run serve
```

## Advanced config schema

If you want modify shema, please see this [document](https://docs.aws.amazon.com/appsync/latest/devguide/building-a-client-app.html)
