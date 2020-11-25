"""AWS integration for S3."""
import asyncio
import logging
import os
import voluptuous as vol

import boto3

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import SOURCE_USER, ConfigEntry

_LOGGER = logging.getLogger(__name__)

CONF_BUCKET = "bucket"
CONF_REGION = "region_name"
CONF_ACCESS_KEY_ID = "aws_access_key_id"
CONF_SECRET_ACCESS_KEY = "aws_secret_access_key"
DOMAIN = "s3"
FILE_PATH = "file_path"
STORAGE_CLASS = "storage_class"
PUT_SERVICE = "put"

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

REQUIREMENTS = ["boto3 == 1.9.69"]

S3_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(SUPPORTED_REGIONS),
        vol.Required(CONF_ACCESS_KEY_ID): cv.string,
        vol.Required(CONF_SECRET_ACCESS_KEY): cv.string,
        vol.Required(CONF_BUCKET): cv.string,
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
        bucket = call.data.get(CONF_BUCKET)
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
            if entry.data[CONF_BUCKET] == call.data[CONF_BUCKET]:
                s3_client = hass.data[DOMAIN][entry.entry_id]
                break
        if s3_client is None:
            _LOGGER.error("S3 client instance not found")
            return

        file_name = os.path.basename(file_path)
        extra_args = {"StorageClass": storage_class}
        try:
            s3_client.upload_file(Filename=file_path, Bucket=bucket, Key=file_name, ExtraArgs=extra_args)
            _LOGGER.info(f"Put file {file_name} to S3 bucket {bucket} using storage class {storage_class}")
        except boto3.exceptions.S3UploadFailedError as err:
            _LOGGER.error(f"S3 upload error: {err}")

    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, PUT_SERVICE, put_file)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    import boto3

    aws_config = {
        CONF_REGION: entry.data[CONF_REGION],
        CONF_ACCESS_KEY_ID: entry.data[CONF_ACCESS_KEY_ID],
        CONF_SECRET_ACCESS_KEY: entry.data[CONF_SECRET_ACCESS_KEY],
    }

    bucket = entry.data[CONF_BUCKET]

    _LOGGER.debug("AWS config for bucket [%s]: %s", bucket, {**aws_config, CONF_SECRET_ACCESS_KEY: "SHH_ITS_A_SECRET"})

    client = boto3.client("s3", **aws_config)  # Will not raise error.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].remove(entry.entry_id)

    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, PUT_SERVICE)

    return True
