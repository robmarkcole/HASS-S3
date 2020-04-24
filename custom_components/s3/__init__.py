"""AWS platform for S3.
https://github.com/home-assistant/example-custom-config/blob/master/custom_components/expose_service_async/__init__.py
"""
import asyncio
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

CONF_BUCKET = "bucket"
CONF_REGION = "region_name"
CONF_ACCESS_KEY_ID = "aws_access_key_id"
CONF_SECRET_ACCESS_KEY = "aws_secret_access_key"
DOMAIN = "s3"
FILE_PATH = "file_path"

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
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-2",
    "ap-northeast-1",
    "ap-south-1",
    "sa-east-1",
]

REQUIREMENTS = ["boto3 == 1.9.69"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(
                    SUPPORTED_REGIONS
                ),
                vol.Required(CONF_ACCESS_KEY_ID): cv.string,
                vol.Required(CONF_SECRET_ACCESS_KEY): cv.string,
                vol.Required(CONF_BUCKET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


@asyncio.coroutine
async def async_setup(hass, config):
    """Set up S3."""
    conf = config[DOMAIN]

    import boto3

    aws_config = {
        CONF_REGION: conf[CONF_REGION],
        CONF_ACCESS_KEY_ID: conf[CONF_ACCESS_KEY_ID],
        CONF_SECRET_ACCESS_KEY: conf[CONF_SECRET_ACCESS_KEY],
    }

    bucket = conf[CONF_BUCKET]
    client = boto3.client("s3", **aws_config)  # Will not raise error.

    def put_file(call):
        """Put file to S3."""
        file_path = call.data.get(FILE_PATH)

        if not hass.config.is_allowed_path(file_path):
            _LOGGER.error("Invalid file_path %s", file_path)
            return

        client.upload_file(Filename=file_path, Bucket=bucket, Key="test2.jpg")
        _LOGGER.info(f"Put file {file_path} to S3 bucket {bucket}")

    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, "put", put_file)

    return True
