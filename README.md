# HASS-S3
Home Assistant integration for AWS S3.

Provides a service for uploading files to a configured S3 bucket. Create your S3 bucket via the AWS console, remember bucket names must be unique.

Add to your `configuration.yaml`:
```
s3:
  aws_access_key_id: AWS_ACCESS_KEY
  aws_secret_access_key: AWS_SECRET_KEY
  region_name: eu-west-1 # optional region, default is us-east-1
  bucket: your_bucket_id
```

## Services
The s3 entity exposes a `put` service for uploading files to S3. The key for the uploaded file will be the file name.

Example data for service call:

```
{
  "file_path":"/some/path/file.jpg"
}
```

The file will be put in the configured bucket with key `file.jpg`

## Accessing S3
I recommend [Filezilla](https://filezilla-project.org/) for connecting to your S3 bucket, free version is available.