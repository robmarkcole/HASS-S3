# HASS-S3
This custom integration provides a service for interacting with S3 including uploading files to a bucket or moving them between folders and buckets. 

Create your S3 bucket via the AWS console, remember bucket names must be unique. I created a bucket with the default access settings (allpublic OFF) and created a bucket name with format `my-bucket-ransom_number` with `random_number` generated [on this website](https://onlinehashtools.com/generate-random-md5-hash).

**Note** for a local and self-hosted alternative checkout the official [Minio integration](https://www.home-assistant.io/integrations/minio/).

## Installation and configuration
Place the `custom_components` folder in your configuration directory (or add its contents to an existing custom_components folder). Add to your Home Assistant configuration UI or add to your `configuration.yaml`:
```yaml
s3:
  aws_access_key_id: AWS_ACCESS_KEY
  aws_secret_access_key: AWS_SECRET_KEY
  region_name: eu-west-1 # optional region, default is us-east-1
```

## Services
### Put Service
The s3 entity exposes a `put` service for uploading files to S3.

Example data for service call:

```
{
  "bucket": "my_bucket",
  "key": "my_key/file.jpg",
  "file_path": "/some/path/file.jpg",
  "storage_class": "STANDARD_IA" # optional
}
```

### Copy Service
The s3 entity exposes a `copy` service for moving files around in S3.

Example data for service call:
```
{
  "bucket": "my_bucket",
  "key_source": "my_key/file_source.jpg",  
  "key_destination": "my_key/file_destination.jpg"
}
```

If you need to move items between buckets use this syntax:
```
{
  "bucket_source": "my_source_bucket",
  "key_source": "my_key/file_source.jpg",
  "bucket_destintation": "my_destination_bucket",
  "key_destination": "my_key/file_destination.jpg"
}
```

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
      bucket: "my_bucket"
      key: "input/{{ now().year }}/{{ (now().month | string).zfill(2) }}/{{ (now().day | string).zfill(2) }}/{{ trigger.event.data.file }}"
      file_path: "{{ trigger.event.data.path }}"
      storage_class: "STANDARD_IA"
```
Note you must configure `folder_watcher`.

## Accessing S3
I recommend [Filezilla](https://filezilla-project.org/) for connecting to your S3 bucket, free version is available.