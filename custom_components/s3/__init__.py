"""AWS platform for S3."""

import base64
import io
import json
import logging
import os
import voluptuous as vol

from homeassistant.core import split_entity_id
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

CONF_BUCKET = "bucket"
CONF_REGION = "region_name"
CONF_ACCESS_KEY_ID = "aws_access_key_id"
CONF_SECRET_ACCESS_KEY = "aws_secret_access_key"

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

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(SUPPORTED_REGIONS),
        vol.Required(CONF_ACCESS_KEY_ID): cv.string,
        vol.Required(CONF_SECRET_ACCESS_KEY): cv.string,
        vol.Required(CONF_BUCKET): cv.string,
    }
)


def setup_platform(hass, config, discovery_info=None):
    """Set up S3."""

    import boto3

    aws_config = {
        CONF_REGION: config.get(CONF_REGION),
        CONF_ACCESS_KEY_ID: config.get(CONF_ACCESS_KEY_ID),
        CONF_SECRET_ACCESS_KEY: config.get(CONF_SECRET_ACCESS_KEY),
    }

    client = boto3.client("s3", **aws_config)  # Will not raise error.

    entities = []
    entities.append(S3(client, config.get(BUCKET),))
    add_devices(entities)


class S3(Entity):
    """Implementation of a file sensor."""

    def __init__(self, client, bucket):
        """Initialize the file sensor."""
        self._client = client
        self._bucket = bucket
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr["bucket"] = self._bucket
        return attr

    @property
    def name(self):
        """Return the name of the S3 entity."""
        return self._name
