# HASS-S3
Home Assistant integration for AWS S3.

This custom integration provides a service for uploading files to a configured S3 bucket. Create your S3 bucket via the AWS console, remember bucket names must be unique. I created a bucket with the default access settings (allpublic OFF) and created a bucket name with format `my-bucket-ransom_number` with `random_number` generated [on this website](https://onlinehashtools.com/generate-random-md5-hash).

## Installation and configuration
Place the custom_components folder in your configuration directory (or add its contents to an existing custom_components folder). Add to your `configuration.yaml`:
```yaml
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

## Example automation
The following automation uses the [folder_watcher](https://www.home-assistant.io/integrations/folder_watcher/) to automatically upload files created in the local filesystem to S3:

```yaml
- id: '1587784389530'
  alias: upload-file-to-S3
  description: 'When a new file is created, upload to S3'
  trigger:
    event_type: folder_watcher
    platform: event
    event_data:
      event_type: created
  action:
    service: s3.put
    data_template:
      file_path: "{{ trigger.event.data.path }}"
```
Note you must configure `folder_watcher`.

## Accessing S3
I recommend [Filezilla](https://filezilla-project.org/) for connecting to your S3 bucket, free version is available.