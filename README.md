# Static S3 website using CDKTF for Python

This repo contains CDKTF code using Python to deploy a static html website to S3.

## Project local setup
1. Make sure node, npm and cdktf are installed
2. Create & activate venv:
    ```
    python3 -m venv .env
    source .env/bin/activate
    ```
3. Install pip dependencies:
    ```
    pip install -r requirements.txt
    ```

4. Set environment variables for AWS authentication:
    ```
    export AWS_ACCESS_KEY_ID=
    export AWS_SECRET_ACCESS_KEY=
    ```


## Running code
1. If you're running Node 23.x.x which isn't considered stable by CDKTF, following may be necessary:
    ```
    export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=true
    ```

2. Deploy infrastructure:
    ```
    cdktf deploy
    ```

## Further improvement ideas
1. Use CloudFront to serve static files and enforce HTTPS
2. Add unit tests implementation
3. Implement CI/CD with tf plan reviews and/or approvals