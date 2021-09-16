"""AWS integration for S3."""
import asyncio
import logging
import os
import voluptuous as vol

import boto3
import botocore

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import SOURCE_USER, ConfigEntry

_LOGGER = logging.getLogger(__name__)

CONF_REGION = "region_name"
CONF_ACCESS_KEY_ID = "aws_access_key_id"
CONF_SECRET_ACCESS_KEY = "aws_secret_access_key"

BUCKET = "bucket"
BUCKET_SOURCE = "bucket_source"
BUCKET_DESTINATION = "bucket_destination"
DOMAIN = "s3"
FILE_PATH = "file_path"
KEY = "key"
KEY_SOURCE = "key_source"
KEY_DESTINATION = "key_destination"
PUT_SERVICE = "put"
COPY_SERVICE = "copy"
STORAGE_CLASS = "storage_class"


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
    "GLACIER",
    "DEEP_ARCHIVE",
]

REQUIREMENTS = ["boto3==1.9.252"]

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


    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, PUT_SERVICE, put_file)
    hass.services.async_register(DOMAIN, COPY_SERVICE, copy_file)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    import boto3

    aws_config = {
        CONF_REGION: entry.data[CONF_REGION],
        CONF_ACCESS_KEY_ID: entry.data[CONF_ACCESS_KEY_ID],
        CONF_SECRET_ACCESS_KEY: entry.data[CONF_SECRET_ACCESS_KEY],
    }
    client = boto3.client("s3", **aws_config)  # Will not raise error.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].remove(entry.entry_id)

    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, PUT_SERVICE)
    return True
