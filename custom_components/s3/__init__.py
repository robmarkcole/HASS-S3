"""AWS integration for S3."""
import asyncio
import logging
import os
import voluptuous as vol
import boto3
import botocore
from botocore.client import Config

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import SOURCE_USER, ConfigEntry

_LOGGER = logging.getLogger(__name__)

CONF_REGION = "region_name"
CONF_ACCESS_KEY_ID = "aws_access_key_id"
CONF_SECRET_ACCESS_KEY = "aws_secret_access_key"

DOMAIN = "s3"
COPY_SERVICE = "copy"
PUT_SERVICE = "put"
DELETE_SERVICE = "delete"
SIGN_SERVICE = "signurl"

BUCKET = "bucket"
BUCKET_SOURCE = "bucket_source"
BUCKET_DESTINATION = "bucket_destination"
FILE_PATH = "file_path"
KEY = "key"
KEY_DESTINATION = "key_destination"
KEY_SOURCE = "key_source"
STORAGE_CLASS = "storage_class"
CONTENT_TYPE = "content_type"
DURATION = "duration"
MESSAGE = "message"
TAGS = "tags"
DEFAULT_REGION = "us-east-1"
SUPPORTED_REGIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ca-central-1",
    "eu-west-1",
    "eu-central-1",
    "eu-west-2",
    "eu-west-3",
    "eu-north-1",
    "eu-south-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-2",
    "ap-northeast-1",
    "ap-south-1",
    "sa-east-1",
]

STORAGE_CLASSES = [
    "STANDARD",
    "REDUCED_REDUNDANCY",
    "STANDARD_IA",
    "ONEZONE_IA",
    "INTELLIGENT_TIERING",
    "GLACIER_IR",
    "GLACIER",
    "DEEP_ARCHIVE",
]

S3_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(SUPPORTED_REGIONS),
        vol.Required(CONF_ACCESS_KEY_ID): cv.string,
        vol.Required(CONF_SECRET_ACCESS_KEY): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.All(cv.ensure_list, [S3_SCHEMA])}, extra=vol.ALLOW_EXTRA,)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up S3."""

    if DOMAIN in config:
        for entry in config[DOMAIN]:
            hass.async_create_task(
                hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER}, data=entry)
            )

    def put_file(call):
        """Put file to S3."""
        bucket = call.data.get(BUCKET)
        key = call.data.get(KEY)
        file_path = call.data.get(FILE_PATH)
        storage_class = call.data.get(STORAGE_CLASS, "STANDARD")
        content_type = call.data.get(CONTENT_TYPE)
        tag_list = call.data.get(TAGS)
        if storage_class not in STORAGE_CLASSES:
            _LOGGER.error("Invalid storage class %s", storage_class)
            return

        if not hass.config.is_allowed_path(file_path):
            _LOGGER.error("Invalid file_path %s", file_path)
            return

        s3_client = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            s3_client = hass.data[DOMAIN][entry.entry_id]
            break
        if s3_client is None:
            _LOGGER.error("S3 client instance not found")
            return

        file_name = os.path.basename(file_path)

        extra_args = {"StorageClass": storage_class}
        if content_type:
            extra_args.update({"ContentType": content_type})
            _LOGGER.debug(
                f"Using content-type {content_type}  upload {file_name}"
            )
        if tag_list:
            extra_args.update({"Tagging": tag_list})
            _LOGGER.debug(
                f"Adding tags {tag_list} for file: {file_name}"
            )

        try:
            s3_client.upload_file(Filename=file_path, Bucket=bucket, Key=key, ExtraArgs=extra_args)
            _LOGGER.info(
                f"Put file {file_name} to S3 bucket {bucket} with key {key} using storage class {storage_class}"
            )
        except botocore.exceptions.ClientError as err:
            _LOGGER.error(f"S3 upload error: {err}")

    def copy_file(call):
        """Copy a file on S3."""
        bucket_source = call.data.get(BUCKET_SOURCE)
        if bucket_source is None:
            bucket_source = call.data.get(BUCKET)

        bucket_destination = call.data.get(BUCKET_DESTINATION)
        if bucket_destination is None:
            bucket_destination = call.data.get(BUCKET)

        key_source = call.data.get(KEY_SOURCE)
        key_destination = call.data.get(KEY_DESTINATION)

        if bucket_source is None or bucket_destination is None or key_source is None or key_destination is None:
            _LOGGER.error(
                f"Invalid copy paramaters from {bucket_source}/{key_source} to {bucket_destination}/{key_destination}"
            )
            return

        s3_client = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            s3_client = hass.data[DOMAIN][entry.entry_id]
            break
        if s3_client is None:
            _LOGGER.error("S3 client instance not found")
            return

        copy_source = {
            'Bucket': bucket_source,
            'Key': key_source
        }

        try:
            s3_client.copy(copy_source, bucket_destination, key_destination)
            _LOGGER.info(
                f"Copied file {bucket_source}/{key_source} to {bucket_destination}/{key_destination}"
            )
        except botocore.exceptions.ClientError as err:
            _LOGGER.error(f"S3 copy error: {err}")

    def delete_file(call):
        """Put file to S3."""
        bucket = call.data.get(BUCKET)
        key = call.data.get(KEY)

        s3_client = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            s3_client = hass.data[DOMAIN][entry.entry_id]
            break
        if s3_client is None:
            _LOGGER.error("S3 client instance not found")
            return

        try:
            s3_client.delete_object(Key=key, Bucket=bucket)
            _LOGGER.info(
                f"Delete file with key {key} from S3 bucket {bucket}"
            )
        except botocore.exceptions.ClientError as err:
            _LOGGER.error(f"S3 delete error: {err}")

    def create_presigned_url(call):
        """Generate a presigned URL to share an S3 object

        :param bucket_name: string
        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """
        bucket = call.data.get(BUCKET)
        key = call.data.get(KEY)
        duration = call.data.get(DURATION)
        message = call.data.get(MESSAGE)

    # Generate a presigned URL for the S3 object
        s3_client = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            s3_client = hass.data[DOMAIN][entry.entry_id]
            break
        if s3_client is None:
            _LOGGER.error("S3 client instance not found")
            return

        try:
            URL = s3_client.generate_presigned_url('get_object',
                                        Params={'Bucket': bucket,
                                                'Key': key},
                                        ExpiresIn=duration)
            _LOGGER.info(
                f"Created SignedUrl of {URL} for file with key {key} from S3 bucket {bucket}"
            )
        except botocore.exceptions.ClientError as err:
            _LOGGER.error(f"SignedURL error: {err}")
    ## Fire event to Home Assistant event bus with type s3_signed_url with URL key and data value
        hass.bus.fire("s3_signed_url", {
            "URL": URL,
            MESSAGE: message,
        })

    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, PUT_SERVICE, put_file)
    hass.services.async_register(DOMAIN, COPY_SERVICE, copy_file)
    hass.services.async_register(DOMAIN, DELETE_SERVICE, delete_file)
    hass.services.async_register(DOMAIN, SIGN_SERVICE, create_presigned_url)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    aws_config = {
        CONF_REGION: entry.data.get(CONF_REGION, DEFAULT_REGION),
        CONF_ACCESS_KEY_ID: entry.data[CONF_ACCESS_KEY_ID],
        CONF_SECRET_ACCESS_KEY: entry.data[CONF_SECRET_ACCESS_KEY],
    }

    def boto_client(aws_config: dict):
        # Use signature version 4 for all regions (required for regions other than us-east-1)
        return boto3.client(
            "s3",
            **aws_config,
            config=Config(signature_version='s3v4')
        )

    client = await hass.async_add_executor_job(boto_client, aws_config)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
